"""
Command line interface for the currency trading system.
This module provides a CLI for interacting with the currency trading system.
"""

import sys
import argparse
from typing import Optional

from valutetrade_hub.core.usecases import UserUseCase, PortfolioUseCase, RateUseCase
from valutetrade_hub.core.exceptions import InsufficientFundsError, CurrencyNotFoundError
from valutetrade_hub.core.currencies import is_valid_currency
from valutetrade_hub.parser_service.updater import RatesUpdater


class CLIInterface:
    """Custom command line interface"""
    
    def __init__(self):
        self.user_usecase = UserUseCase()
        self.rate_usecase = RateUseCase()
        self.portfolio_usecase = PortfolioUseCase(self.rate_usecase)
        self.rates_updater = RatesUpdater()
        self.current_user_id: Optional[int] = None
        self.current_username: Optional[str] = None
    
    def run(self, args=None):
        """Start the CLI in interactive mode"""
        if args is not None and len(args) > 0:
            return self._run_command(args)
        else:
            return self._run_interactive()
    
    def _run_command(self, args):
        """Process one command from the command line"""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        return self._handle_command(parsed_args)
    
    def _run_interactive(self):
        """Start the CLI in interactive mode"""
        print("Welcome to the currency portfolio management system!")
        print("Enter 'help' for a list of commands or 'exit' to quit.")
        
        while True:
            try:
                prompt = ""
                if self.current_username:
                    prompt = f"{self.current_username}> "
                else:
                    prompt = "> "
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                if user_input.lower() in ['help', 'h']:
                    self._print_help()
                    continue
                
                command_args = user_input.split()
                parser = self._create_parser()
                
                try:
                    parsed_args = parser.parse_args(command_args)
                    self._handle_command(parsed_args)
                except SystemExit:
                    # argparse calls SystemExit on errors, continue working
                    pass
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break
    
    def _create_parser(self):
        """Create parser for command line interface"""
        parser = argparse.ArgumentParser(description='Currency portfolio management system', add_help=False)
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Registration command
        register_parser = subparsers.add_parser('register', help='Register a new user')
        register_parser.add_argument('--username', required=True, help='Username')
        register_parser.add_argument('--password', required=True, help='Password')
        
        # Login command
        login_parser = subparsers.add_parser('login', help='Login to the system')
        login_parser.add_argument('--username', required=True, help='Username')
        login_parser.add_argument('--password', required=True, help='Password')
        
        # Portfolio view command
        portfolio_parser = subparsers.add_parser('show-portfolio', help='Show portfolio')
        portfolio_parser.add_argument('--base', default='USD', help='Base currency (default USD)')
        
        # Currency purchase command
        buy_parser = subparsers.add_parser('buy', help='Buy currency')
        buy_parser.add_argument('--currency', required=True, help='Currency code')
        buy_parser.add_argument('--amount', type=float, required=True, help='Amount of currency')
        
        # Currency sale command
        sell_parser = subparsers.add_parser('sell', help='Sell currency')
        sell_parser.add_argument('--currency', required=True, help='Currency code')
        sell_parser.add_argument('--amount', type=float, required=True, help='Amount of currency')
        
        # Exchange rate command
        rate_parser = subparsers.add_parser('get-rate', help='Get currency rate')
        rate_parser.add_argument('--from', dest='from_currency', required=True, help='Source currency')
        rate_parser.add_argument('--to', dest='to_currency', required=True, help='Target currency')
        
        # Rate update command
        update_rates_parser = subparsers.add_parser('update-rates', help='Update currency rates')
        update_rates_parser.add_argument('--source', choices=['coingecko', 'exchangerate'],
                                            help='Source for update (coingecko or exchangerate)')
        
        # Rate display command
        show_rates_parser = subparsers.add_parser('show-rates', help='Show current rates')
        show_rates_parser.add_argument('--currency', help='Show rate only for the specified currency')
        show_rates_parser.add_argument('--top', type=int, help='Show top N most expensive cryptocurrencies')
        show_rates_parser.add_argument('--base', default='USD', help='Base currency (default USD)')
        
        # Help command
        subparsers.add_parser('help', help='Show help')
        
        # Exit command
        subparsers.add_parser('exit', help='Exit the program')
        
        return parser
    
    def _handle_command(self, args):
        """Handle command"""
        if args.command == 'register':
            self._handle_register(args)
        elif args.command == 'login':
            self._handle_login(args)
        elif args.command == 'show-portfolio':
            self._handle_show_portfolio(args)
        elif args.command == 'buy':
            self._handle_buy(args)
        elif args.command == 'sell':
            self._handle_sell(args)
        elif args.command == 'get-rate':
            self._handle_get_rate(args)
        elif args.command == 'help':
            self._print_help()
        elif args.command == 'exit':
            print("Goodbye!")
            sys.exit(0)
        elif args.command == 'update-rates':
            self._handle_update_rates(args)
        elif args.command == 'show-rates':
            self._handle_show_rates(args)
        else:
            self._print_help()
    
    def _print_help(self):
        """Show help message"""
        help_text = """
 Available commands:
   register --username USERNAME --password PASSWORD  Register a new user
   login --username USERNAME --password PASSWORD     Login to the system
   show-portfolio [--base BASE]                     Show portfolio
   buy --currency CURRENCY --amount AMOUNT             Buy currency
   sell --currency CURRENCY --amount AMOUNT           Sell currency
   get-rate --from FROM --to TO                      Get currency rate
   update-rates [--source SOURCE]                   Update currency rates
   show-rates [--currency CURRENCY] [--top N] [--base BASE]  Show current rates
   help                                              Show this help
   exit                                              Exit the program
        """
        print(help_text.strip())
    
    def _handle_register(self, args):
        """Handle register command"""
        try:
            success, message = self.user_usecase.register_user(args.username, args.password)
            print(message)
        except Exception as e:
            print(f"Registration error: {e}")
    
    def _handle_login(self, args):
        """Handle login command"""
        try:
            success, message = self.user_usecase.login_user(args.username, args.password)
            print(message)
            if success:
                # Store user info for future commands
                self.current_username = args.username
                # We'll get the user_id when we need it by looking it up
        except Exception as e:
            print(f"Login error: {e}")
    
    def _get_current_user_id(self):
        """Get current user ID from username"""
        if not self.current_username:
            return None
        
        users = self.user_usecase.db_manager.load_users()
        user = users.get(self.current_username)
        if user:
            return user.user_id
        return None
    
    def _handle_show_portfolio(self, args):
        """Handle show-portfolio command"""
        if not self.current_username:
            print("Please login first")
            return
        
        try:
            user_id = self._get_current_user_id()
            if user_id is None:
                print("Error: Failed to get user information")
                return
                
            success, message = self.portfolio_usecase.get_portfolio_info(user_id, args.base)
            print(message)
        except CurrencyNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error getting portfolio: {e}")
    
    def _handle_buy(self, args):
        """Handle buy command"""
        if not self.current_username:
            print("Please login first")
            return
        
        try:
            # Validate currency
            if not is_valid_currency(args.currency):
                print(f"Error: Unsupported currency '{args.currency}'")
                return
            
            user_id = self._get_current_user_id()
            if user_id is None:
                print("Error: Failed to get user information")
                return
                
            success, message = self.portfolio_usecase.buy_currency(user_id, args.currency.upper(), args.amount)
            print(message)
        except InsufficientFundsError as e:
            print(f"Error: {e}")
        except CurrencyNotFoundError as e:
            print(f"Error: {e}")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error buying currency: {e}")
    
    def _handle_sell(self, args):
        """Handle sell command"""
        if not self.current_username:
            print("Please login first")
            return
        
        try:
            # Validate currency
            if not is_valid_currency(args.currency):
                print(f"Error: Unsupported currency '{args.currency}'")
                return
            
            user_id = self._get_current_user_id()
            if user_id is None:
                print("Error: Failed to get user information")
                return
                
            success, message = self.portfolio_usecase.sell_currency(user_id, args.currency.upper(), args.amount)
            print(message)
        except InsufficientFundsError as e:
            print(f"Error: {e}")
        except CurrencyNotFoundError as e:
            print(f"Error: {e}")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error selling currency: {e}")
    
    def _handle_get_rate(self, args):
        """Handle get-rate command"""
        try:
            # Validate currencies
            if not is_valid_currency(args.from_currency):
                print(f"Error: Unsupported currency '{args.from_currency}'")
                return
            
            if not is_valid_currency(args.to_currency):
                print(f"Error: Unsupported currency '{args.to_currency}'")
                return
            
            success, message = self.rate_usecase.get_exchange_rate(args.from_currency.upper(), args.to_currency.upper())
            print(message)
        except CurrencyNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error getting rate: {e}")
    
    def _handle_update_rates(self, args):
        """Handle update-rates command"""
        try:
            print("INFO: Starting rates update...")
            result = self.rates_updater.run_update(source=args.source)
            
            if result["errors"]:
                print("Update completed with errors. Check logs for details.")
            else:
                print(f"Update successful. Total rates updated: {result['updated_count']}. Last refresh: {result['last_refresh']}")
        except Exception as e:
            print(f"Error updating rates: {e}")
    
    def _handle_show_rates(self, args):
        """Handle show-rates command"""
        try:
            # Get rate summary
            summary = self.rates_updater.get_rates_summary()
            
            # Check if there is data
            if not summary["pairs"]:
                print("Local rate cache is empty. Run 'update-rates' to load data.")
                return
            
            # Filter data by parameters
            filtered_pairs = summary["pairs"]
            
            # Currency filter
            if args.currency:
                filtered_pairs = {
                    pair: data for pair, data in summary["pairs"].items()
                    if args.currency.upper() in pair
                }
                
                if not filtered_pairs:
                    print(f"Rate for '{args.currency.upper()}' not found in cache.")
                    return
            
            # Sort for top-N
            if args.top:
                # Sort by rate value (descending)
                sorted_pairs = sorted(
                    filtered_pairs.items(),
                    key=lambda x: x[1]["rate"],
                    reverse=True
                )
                # Take only top-N
                sorted_pairs = sorted_pairs[:args.top]
                # Convert back to dictionary
                filtered_pairs = dict(sorted_pairs)
            
            # Display results
            print(f"Rates from cache (updated at {summary['last_refresh']}):")
            for pair, data in filtered_pairs.items():
                # Check base currency
                if args.base and f"_{args.base.upper()}_" not in f"_{pair}_":
                    continue
                print(f"- {pair}: {data['rate']}")
                
        except Exception as e:
            print(f"Error getting rates: {e}")
def main():
    """CLI entry point"""
    import sys
    cli = CLIInterface()
    cli.run(sys.argv[1:])




if __name__ == '__main__':
    main()