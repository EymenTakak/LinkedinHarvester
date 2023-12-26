from playwright.sync_api import Playwright, sync_playwright, expect
from time import sleep
import os
from bs4 import BeautifulSoup
import pandas as pd
import json
from colorama import Fore, Style, init

init(autoreset=True)
class CommandLineTool:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.page_numbers = 0
        self.target_url = ""

    def print_welcome_message(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"""{Fore.GREEN}
    | |    (_) _ __  | | __ ___   __| |(_) _ __          
    | |    | || '_ \ | |/ // _ \ / _` || || '_ \         
    | |___ | || | | ||   <|  __/| (_| || || | | |        
    |_____||_||_| |_||_|\_\\___| \__,_||_||_| |_|        
    | | | |  __ _  _ __ __   __ ___  ___ | |_  ___  _ __ 
    | |_| | / _` || '__|\ \ / // _ \/ __|| __|/ _ \| '__|
    |  _  || (_| || |    \ V /|  __/\__ \| |_|  __/| |   
    |_| |_| \__,_||_|     \_/  \___||___/ \__|\___||_|   


              
            Version    : 1.0
            Author     : Eymen Takak
            Licence    : MIT License
            Note       : pip install -r requirements.txt
            
    Welcome! Type 'help' to see the available commands.
              
              {Style.RESET_ALL}""")


    def print_help_message(self):
        print(f"\n{Fore.BLUE}Available Commands:")
        print(f"  {Fore.CYAN}help{Style.RESET_ALL}: Show this help message.")
        print(f"  {Fore.CYAN}options{Style.RESET_ALL}: Display entered values.")
        print(f"  {Fore.CYAN}set username [value]{Style.RESET_ALL}: Set the username.")
        print(f"  {Fore.CYAN}set password [value]{Style.RESET_ALL}: Set the password.")
        print(f"  {Fore.CYAN}set page [value]{Style.RESET_ALL}: Set the page number.")
        print(f"  {Fore.CYAN}set url [value]{Style.RESET_ALL}: Set the target URL.")
        print(f"  {Fore.CYAN}run{Style.RESET_ALL}: Run the harvester function.")
        print(f"  {Fore.CYAN}clear{Style.RESET_ALL}: Clear the console screen.")
        print(f"  {Fore.CYAN}exit{Style.RESET_ALL}: Exit the program.\n")

    def print_options(self):
        print(f"\n{Fore.YELLOW}Entered Values:")
        print(f"  {Fore.MAGENTA}Username:{Style.RESET_ALL} {self.username}")
        print(f"  {Fore.MAGENTA}Password:{Style.RESET_ALL} ********")
        print(f"  {Fore.MAGENTA}Page Number:{Style.RESET_ALL} {self.page_numbers}")
        print(f"  {Fore.MAGENTA}Target URL:{Style.RESET_ALL} {self.target_url}\n")

    def set_username(self, value):
        self.username = value
        print(f"{Fore.GREEN}Username set to '{self.username}'.{Style.RESET_ALL}")

    def set_password(self, value):
        self.password = value
        print(f"{Fore.GREEN}Password set successfully.{Style.RESET_ALL}")

    def set_page_numbers(self, value):
        try:
            self.page_numbers = int(value)
            print(f"{Fore.GREEN}Page number set to {self.page_numbers}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid number format.{Style.RESET_ALL}")

    def set_target_url(self, value):
        self.target_url = value
        print(f"{Fore.GREEN}Target URL set to '{self.target_url}'.{Style.RESET_ALL}")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Fore.GREEN}Console screen cleared.{Style.RESET_ALL}")

    def scrape_page_data(self,page_content):
        soup = BeautifulSoup(page_content, 'html.parser')

        results = soup.select('.reusable-search__result-container')

        data_list = []
        for result in results:
            name_div = result.select_one('.entity-result__title-text.t-16')
            name = name_div.select_one('span[aria-hidden="true"]')

            title = result.select_one('.entity-result__primary-subtitle.t-14.t-black.t-normal')
            location = result.select_one('.entity-result__secondary-subtitle.t-14.t-normal')
            minfo = result.select_one('.entity-result__summary.entity-result__summary--2-lines.t-12.t-black--light')

            data_list.append({
                'name': name.get_text(strip=True) if name else None,
                'title': title.get_text(strip=True) if title else None,
                'location': location.get_text(strip=True) if location else None,
                'Minfo': minfo.get_text(strip=True) if minfo else None
            })

        return data_list

    def run(self,playwright: Playwright) -> None:
        browser = playwright.firefox.launch(headless=False)
        context = browser.new_context()

        page = context.new_page()

        page.goto("https://www.linkedin.com/")
        page.get_by_label("Email or phone", exact=True).click()
        page.get_by_label("Email or phone", exact=True).fill(self.username)
        page.get_by_label("Password", exact=True).click()
        page.get_by_label("Password", exact=True).fill(self.password)

        page.get_by_role("button", name="Sign in").click()
        sleep(0.5)
        page.wait_for_load_state("load")

        page.goto(self.target_url)
        page.wait_for_load_state()
        page_content = page.content()

        all_data_in = {}
        for i in range(self.page_numbers):
            page_content = page.content()
            data = self.scrape_page_data(page_content)
            all_data_in[f"page_{i + 1}"] = data
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.locator(f'[data-test-pagination-page-btn="{i + 1}"]').click()
            page.wait_for_selector(".reusable-search__result-container")
            sleep(2)

        unique_items = set()

        for page, items in all_data_in.items():
            unique_page_items = []
            for item in items:
                item_tuple = tuple(item.items())
                if item_tuple not in unique_items:
                    unique_page_items.append(item)
                    unique_items.add(item_tuple)
            all_data_in[page] = unique_page_items

        flat_data = [item for sublist in all_data_in.values() for item in sublist]
        df = pd.DataFrame(flat_data)
        df.to_excel('output.xlsx', index=False)

        with open('output.txt', 'w', encoding='utf-8') as file:
            for page, page_data in all_data_in.items():
                file.write(f"{page}:\n")
                for item in page_data:
                    file.write(f"  {item}\n")
                file.write("\n")

        with open('output.json', 'w', encoding='utf-8') as json_file:
            json.dump(all_data_in, json_file, indent=2, ensure_ascii=False)
        # ---------------------
        browser.close()
        print(f"{Fore.YELLOW}Files Saved. (output.json, output.txt, output.xlsx){Style.RESET_ALL}")
    def start_function(self):
        try:
            with sync_playwright() as playwright:
                self.run(playwright)
        except Exception as e:
            print(f"{Fore.RED}ERROR.{Style.RESET_ALL}\n\n")
            print(f"{Fore.RED}{e}{Style.RESET_ALL}")


    def process_command(self, command):
        tokens = command.split()
        if not tokens:
            return

        if tokens[0] == "help":
            self.print_help_message()
        elif tokens[0] == "options":
            self.print_options()
        elif tokens[0] == "set":
            if len(tokens) >= 3:
                if tokens[1] == "username":
                    self.set_username(tokens[2])
                elif tokens[1] == "password":
                    self.set_password(tokens[2])
                elif tokens[1] == "page":
                    self.set_page_numbers(tokens[2])
                elif tokens[1] == "url":
                    self.set_target_url(tokens[2])
                else:
                    print(f"{Fore.RED}Invalid command.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Invalid command format.{Style.RESET_ALL}")
        elif tokens[0] == "run":
            if all([self.username, self.password, self.page_numbers, self.target_url]):
                self.start_function()
            else:
                print(f"{Fore.RED}Please fill in all the information.{Style.RESET_ALL}")

        elif tokens[0] == "clear":
            self.clear_screen()
        elif tokens[0] == "exit":
            os.system('cls' if os.name == 'nt' else 'clear')
            exit()
        else:
            print(f"{Fore.RED}Invalid command.{Style.RESET_ALL}")

if __name__ == "__main__":
    tool = CommandLineTool()
    tool.print_welcome_message()

    while True:
        command = input(f"{Fore.CYAN}>{Style.RESET_ALL} ")
        tool.process_command(command)
