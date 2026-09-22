import argparse
import sys

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Green AI Simulator - Generación sintética determinista de métricas"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Subcomando 'validate'
    validate_parser = subparsers.add_parser("validate", help="Valida un inventario y configuración de escenario")
    validate_parser.add_argument("--inventory", required=True, help="Ruta al archivo JSON de inventario")
    validate_parser.add_argument("--scenario", required=True, help="Ruta al archivo JSON de escenario")
    
    # Subcomando 'run'
    run_parser = subparsers.add_parser("run", help="Ejecuta una simulación")
    run_parser.add_argument("--inventory", required=True, help="Ruta al archivo JSON de inventario")
    run_parser.add_argument("--scenario", required=True, help="Ruta al archivo JSON de escenario")
    run_parser.add_argument("--seed", type=int, required=True, help="Semilla para la generación determinista")
    run_parser.add_argument("--duration-seconds", type=int, required=True, help="Duración de la simulación en segundos")
    run_parser.add_argument("--tick-seconds", type=int, required=True, help="Resolución (tick) en segundos")
    run_parser.add_argument("--mode", choices=["offline", "realtime"], required=True, help="Modo de ejecución")
    run_parser.add_argument("--output-dir", required=True, help="Directorio donde se guardarán los resultados del run")
    run_parser.add_argument("--host", default="127.0.0.1", help="Host para el exporter HTTP de Prometheus (default: 127.0.0.1)")
    run_parser.add_argument("--port", type=int, default=9090, help="Puerto para el exporter HTTP de Prometheus (default: 9090)")
    
    return parser

def main():
    parser = create_parser()
    
    # Si no se proveen argumentos, mostrar ayuda
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    
    if args.command == "validate":
        print(f"Validating inventory from '{args.inventory}'...")
        try:
            from green_ai_simulator.adapters.configuration.json_parser import parse_inventory_json
            from green_ai_simulator.domain.inventory import validate_inventory, ValidationError
            from green_ai_simulator.adapters.configuration.scenario_parser import parse_scenario_json
            from green_ai_simulator.domain.scenario import validate_scenario
            
            inv = parse_inventory_json(args.inventory)
            validate_inventory(inv)
            print("Inventory validation successful.")
            print(f"Cluster: {inv.cluster_name}")
            print(f"Total Nodes: {len(inv.nodes)}")
            
            print(f"Validating scenario from '{args.scenario}'...")
            scenario = parse_scenario_json(args.scenario)
            validate_scenario(scenario)
            print("Scenario validation successful.")
            print(f"Scenario Name: {scenario.name}")
            print(f"Base CPU Utilization: {scenario.base_cpu_utilization}")
            
            sys.exit(0)
        except ValidationError as e:
            print(f"Validation Error: {e}", file=sys.stderr)
            sys.exit(2)
        except Exception as e:
            print(f"System Error: {e}", file=sys.stderr)
            sys.exit(1)
        
    elif args.command == "run":
        try:
            from green_ai_simulator.application.runner import run_simulation
            sys.exit(run_simulation(args))
        except Exception as e:
            print(f"System Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
