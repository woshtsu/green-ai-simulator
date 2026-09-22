import signal
import sys
import time
from typing import Any
from green_ai_simulator.adapters.configuration.json_parser import parse_inventory_json
from green_ai_simulator.domain.inventory import validate_inventory
from green_ai_simulator.adapters.configuration.scenario_parser import parse_scenario_json
from green_ai_simulator.domain.scenario import validate_scenario
from green_ai_simulator.domain.engine import create_initial_state, compute_next_state
from green_ai_simulator.adapters.persistence.run_logger import RunLogger

def run_simulation(args: Any) -> int:
    try:
        inv = parse_inventory_json(args.inventory)
        validate_inventory(inv)
        scn = parse_scenario_json(args.scenario)
        validate_scenario(scn)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 2

    if args.tick_seconds <= 0:
        print("Error: tick_seconds must be > 0", file=sys.stderr)
        return 2
        
    if args.duration_seconds % args.tick_seconds != 0:
        print("Error: duration_seconds must be a multiple of tick_seconds", file=sys.stderr)
        return 2

    try:
        logger = RunLogger(
            output_dir_base=args.output_dir,
            mode=args.mode,
            seed=args.seed,
            duration_sec=args.duration_seconds,
            tick_sec=args.tick_seconds,
            inv_path=args.inventory,
            scn_path=args.scenario
        )
    except Exception as e:
        print(f"Failed to initialize logger: {e}", file=sys.stderr)
        return 1

    print(f"Run ID: {logger.uuid}")
    print(f"Output directory: {logger.run_dir}")
    print(f"Mode: {args.mode}")
    
    # Setup prometheus in realtime mode
    collector = None
    if args.mode == "realtime":
        try:
            from prometheus_client import start_http_server, REGISTRY
            from green_ai_simulator.adapters.prometheus.exporter import SimulatorCollector
            collector = SimulatorCollector(inv, logger.uuid)
            REGISTRY.register(collector)
            
            # Start http server
            port = getattr(args, "port", 9090)
            host = getattr(args, "host", "127.0.0.1")
            print(f"Starting Prometheus exporter on {host}:{port}/metrics")
            start_http_server(port, addr=host)
        except Exception as e:
            print(f"Failed to start Prometheus exporter: {e}", file=sys.stderr)
            logger.update_status("FAILED", "Prometheus exporter failed")
            logger.close()
            return 1
            
    logger.update_status("RUNNING")
    state = create_initial_state(inv)
    if collector:
        collector.update_state(state)
    
    stop_requested = False
    def handle_sigint(sig, frame):
        nonlocal stop_requested
        print("\nGraceful stop requested (SIGINT/SIGTERM). Please wait for current tick to finish...")
        stop_requested = True
        
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)
    
    try:
        if not logger.write_sample(state):
             logger.update_status("FAILED", "Output size limit reached on initial state")
             logger.close()
             return 1
             
        # Loop monotonic time reference
        next_tick_time = time.monotonic() + args.tick_seconds
             
        while state.logical_time < args.duration_seconds:
            if stop_requested:
                logger.update_status("STOPPED", "User requested stop via signal")
                logger.close()
                if collector:
                    REGISTRY.unregister(collector)
                return 0
                
            if args.mode == "realtime":
                # Realtime delay
                now = time.monotonic()
                sleep_time = next_tick_time - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # Degradation detected: the loop is slower than 1x
                    # We log it but continue immediately
                    pass
                next_tick_time += args.tick_seconds
                
            state = compute_next_state(inv, scn, state, args.seed, args.tick_seconds)
            if collector:
                collector.update_state(state)
            
            if not logger.write_sample(state):
                logger.update_status("FAILED", "Output size limit reached")
                logger.close()
                print("Failed: Output size limit reached", file=sys.stderr)
                if collector:
                    REGISTRY.unregister(collector)
                return 1
                 
        logger.update_status("COMPLETED", "Duration reached")
        print("Simulation COMPLETED.")
        if collector:
            REGISTRY.unregister(collector)
        
    except Exception as e:
        logger.update_status("FAILED", f"Exception during execution: {e}")
        logger.close()
        if collector:
             REGISTRY.unregister(collector)
        raise e
    
    logger.close()
    return 0
