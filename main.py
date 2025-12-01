
from valutetrade_hub.cli.interface import main
import scheduler
from valutetrade_hub.parser_service.updater import RatesUpdater

if __name__ == "__main__":
    # Start the currency rates scheduler
    result = RatesUpdater()
    result.update_rates()
    
    # Start the CLI interface
    main()
