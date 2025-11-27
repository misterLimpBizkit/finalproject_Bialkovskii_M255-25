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


class CLIInterface:
    """Custom command line interface"""
    
    def __init__(self):
        self.user_usecase = UserUseCase()
        self.rate_usecase = RateUseCase()
        self.portfolio_usecase = PortfolioUseCase(self.rate_usecase)
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
        print("Добро пожаловать в систему управления валютным портфелем!")
        print("Введите 'help' для получения списка команд или 'exit' для выхода.")
        
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
                    print("До свидания!")
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
                    # argparse вызывает SystemExit при ошибках, продолжаем работу
                    pass
                    
            except KeyboardInterrupt:
                print("\nДо свидания!")
                break
            except EOFError:
                print("\nДо свидания!")
                break
    
    def _create_parser(self):
        """Create parser for command line interface"""
        parser = argparse.ArgumentParser(description='Система управления валютным портфелем', add_help=False)
        subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
        
        # Команда регистрации
        register_parser = subparsers.add_parser('register', help='Регистрация нового пользователя')
        register_parser.add_argument('--username', required=True, help='Имя пользователя')
        register_parser.add_argument('--password', required=True, help='Пароль')
        
        # Команда входа
        login_parser = subparsers.add_parser('login', help='Вход в систему')
        login_parser.add_argument('--username', required=True, help='Имя пользователя')
        login_parser.add_argument('--password', required=True, help='Пароль')
        
        # Команда просмотра портфеля
        portfolio_parser = subparsers.add_parser('show-portfolio', help='Показать портфель')
        portfolio_parser.add_argument('--base', default='USD', help='Базовая валюта (по умолчанию USD)')
        
        # Команда покупки валюты
        buy_parser = subparsers.add_parser('buy', help='Купить валюту')
        buy_parser.add_argument('--currency', required=True, help='Код валюты')
        buy_parser.add_argument('--amount', type=float, required=True, help='Количество валюты')
        
        # Команда продажи валюты
        sell_parser = subparsers.add_parser('sell', help='Продать валюту')
        sell_parser.add_argument('--currency', required=True, help='Код валюты')
        sell_parser.add_argument('--amount', type=float, required=True, help='Количество валюты')
        
        # Команда получения курса
        rate_parser = subparsers.add_parser('get-rate', help='Получить курс валюты')
        rate_parser.add_argument('--from', dest='from_currency', required=True, help='Исходная валюта')
        rate_parser.add_argument('--to', dest='to_currency', required=True, help='Целевая валюта')
        
        # Команда помощи
        subparsers.add_parser('help', help='Показать помощь')
        
        # Команда выхода
        subparsers.add_parser('exit', help='Выход из программы')
        
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
            print("До свидания!")
            sys.exit(0)
        else:
            self._print_help()
    
    def _print_help(self):
        """Show help message"""
        help_text = """
Доступные команды:
  register --username USERNAME --password PASSWORD  Регистрация нового пользователя
  login --username USERNAME --password PASSWORD     Вход в систему
  show-portfolio [--base BASE]                     Показать портфель
  buy --currency CURRENCY --amount AMOUNT             Купить валюту
  sell --currency CURRENCY --amount AMOUNT           Продать валюту
  get-rate --from FROM --to TO                      Получить курс валюты
  help                                              Показать эту справку
  exit                                              Выход из программы
        """
        print(help_text.strip())
    
    def _handle_register(self, args):
        """Handle register command"""
        try:
            success, message = self.user_usecase.register_user(args.username, args.password)
            print(message)
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
    
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
            print(f"Ошибка входа: {e}")
    
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
            print("Сначала выполните login")
            return
        
        try:
            user_id = self._get_current_user_id()
            if user_id is None:
                print("Ошибка: Не удалось получить информацию о пользователе")
                return
                
            success, message = self.portfolio_usecase.get_portfolio_info(user_id, args.base)
            print(message)
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Ошибка получения портфеля: {e}")
    
    def _handle_buy(self, args):
        """Handle buy command"""
        if not self.current_username:
            print("Сначала выполните login")
            return
        
        try:
            # Validate currency
            if not is_valid_currency(args.currency):
                print(f"Ошибка: Неподдерживаемая валюта '{args.currency}'")
                return
            
            user_id = self._get_current_user_id()
            if user_id is None:
                print("Ошибка: Не удалось получить информацию о пользователе")
                return
                
            success, message = self.portfolio_usecase.buy_currency(user_id, args.currency.upper(), args.amount)
            print(message)
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
        except ValueError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Ошибка покупки валюты: {e}")
    
    def _handle_sell(self, args):
        """Handle sell command"""
        if not self.current_username:
            print("Сначала выполните login")
            return
        
        try:
            # Validate currency
            if not is_valid_currency(args.currency):
                print(f"Ошибка: Неподдерживаемая валюта '{args.currency}'")
                return
            
            user_id = self._get_current_user_id()
            if user_id is None:
                print("Ошибка: Не удалось получить информацию о пользователе")
                return
                
            success, message = self.portfolio_usecase.sell_currency(user_id, args.currency.upper(), args.amount)
            print(message)
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
        except ValueError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Ошибка продажи валюты: {e}")
    
    def _handle_get_rate(self, args):
        """Handle get-rate command"""
        try:
            # Validate currencies
            if not is_valid_currency(args.from_currency):
                print(f"Ошибка: Неподдерживаемая валюта '{args.from_currency}'")
                return
            
            if not is_valid_currency(args.to_currency):
                print(f"Ошибка: Неподдерживаемая валюта '{args.to_currency}'")
                return
            
            success, message = self.rate_usecase.get_exchange_rate(args.from_currency.upper(), args.to_currency.upper())
            print(message)
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Ошибка получения курса: {e}")


def main():
    """Точка входа в CLI"""
    import sys
    cli = CLIInterface()
    cli.run(sys.argv[1:])


if __name__ == '__main__':
    main()