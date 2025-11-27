import sys
import argparse
from typing import Optional
from valutetrade_hub.core.usecases import UserUseCase, PortfolioUseCase, RateUseCase


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
        success, message = self.user_usecase.register_user(args.username, args.password)
        print(message)
        if not success:
            pass
    
    def _handle_login(self, args):
        """Handle login command"""
        success, message = self.user_usecase.login_user(args.username, args.password)
        print(message)
        if success:
            users = self.user_usecase.user_storage.load_users()
            if args.username in users:
                user = users[args.username]
                # Handle both User objects and dictionaries
                if isinstance(user, dict):
                    self.current_user_id = user['user_id']
                else:
                    self.current_user_id = user.user_id
                self.current_username = args.username
        else:
            pass
    
    def _handle_show_portfolio(self, args):
        """Handle show-portfolio command"""
        if self.current_user_id is None:
            print("Сначала выполните login")
            return
        
        success, message = self.portfolio_usecase.get_portfolio_info(self.current_user_id, args.base)
        print(message)
        if not success:
            pass
    
    def _handle_buy(self, args):
        """Handle buy command"""
        if self.current_user_id is None:
            print("Сначала выполните login")
            return
        
        success, message = self.portfolio_usecase.buy_currency(self.current_user_id, args.currency.upper(), args.amount)
        print(message)
        if not success:
            pass
    
    def _handle_sell(self, args):
        """Handle sell command"""
        if self.current_user_id is None:
            print("Сначала выполните login")
            return
        
        success, message = self.portfolio_usecase.sell_currency(self.current_user_id, args.currency.upper(), args.amount)
        print(message)
        if not success:
            pass
    
    def _handle_get_rate(self, args):
        """Handle get-rate command"""
        success, message = self.rate_usecase.get_exchange_rate(args.from_currency.upper(), args.to_currency.upper())
        print(message)
        if not success:
            pass


def main():
    """Точка входа в CLI"""
    import sys
    cli = CLIInterface()
    cli.run(sys.argv[1:])


if __name__ == '__main__':
    main()