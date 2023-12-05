import psycopg2

from model import Model
from view import View


class Controller:
    def __init__(self, connection_settings):  # Startup for model and view
        self.view = View()
        try:
            self.model = Model(connection_settings)
        except psycopg2.Error:
            self.view.show_connection_error()
            exit(-1)

    def run(self):  # Menu
        menu = {
            1: self.view_table,
            2: self.view_all_tables,
            3: self.add_table,
            4: self.delete_table,
            5: self.delete_table,
            6: self.randomize_table,
            7: self.search
        }
        while True:
            choice = self.view.show_menu()
            if choice == 8:
                break
            elif choice in menu:
                menu[choice]()

    def view_table(self):
        try:
            selected = self.view.show_table_menu(self.model.tables)
            table = self.model.get_table(selected)
            self.view.show_table(table)
        except psycopg2.Error as error:
            self.view.show_sql_error(error)

    def view_all_tables(self):
        try:
            for i in self.model.tables:
                table = self.model.get_table(i)
                self.view.show_msg(self.model.tables[i])
                self.view.show_table(table)
        except psycopg2.Error as error:
            self.view.show_sql_error(error)

    def add_table(self):
        try:
            selected = self.view.show_table_menu(self.model.tables)
            table = self.model.get_table(selected)
            self.view.show_table(table)
            needed_params = self.model.get_params(selected)
            entered_params = self.view.show_params_menu(needed_params)
            Verification = self.model.add_table(selected, entered_params)
            if not Verification:
                self.view.show_sanity_error()
        except psycopg2.Error as error:
            self.view.show_sql_error(error)

    def delete_table(self):
        try:
            selected = self.view.show_table_menu(self.model.tables)
            table = self.model.get_table(selected)
            self.view.show_table(table)
            self.view.show_msg("Select id to delete: ")
            id_to_delete = self.view.get_id()
            Verification = self.model.delete_table(selected, id_to_delete)
            if not Verification:
                self.view.show_sanity_error()
        except psycopg2.Error as error:
            self.view.show_sql_error(error)

    def edit_table(self):
        try:
            selected = self.view.show_table_menu(self.model.tables)
            table = self.model.get_table(selected)
            self.view.show_table(table)
            self.view.show_msg("Select id to edit: ")
            id_to_edit = self.view.get_id()
            available_params = self.model.get_params(selected)
            selected_param = self.view.show_params_menu_selection(available_params)
            selected_param_value = self.view.get_param(available_params[selected_param])
            Verification = self.model.edit_table(selected, id_to_edit, selected_param, selected_param_value)
            if not Verification:
                self.view.show_sanity_error()
        except psycopg2.Error as error:
            self.view.show_sql_error(error)

    def randomize_table(self):
        try:
            selected = self.view.show_table_menu(self.model.tables)
            table = self.model.get_table(selected)
            self.view.show_table(table)
            random_count = self.view.show_random_menu()
            self.model.randomize_table(selected, random_count)
        except psycopg2.Error as error:
            self.view.show_sql_error(error)

    def search(self):
        try:
            selected_search_query = self.view.show_table_menu(self.model.tables_for_search)
            available_params = self.model.get_params_for_search(selected_search_query)
            entered_params = self.view.show_params_menu(available_params)
            table, execution_time = self.model.search(selected_search_query, entered_params)
            self.view.show_table(table)
            self.view.show_execution_time(execution_time)
        except psycopg2.Error as error:
            self.view.show_sql_error(error)
