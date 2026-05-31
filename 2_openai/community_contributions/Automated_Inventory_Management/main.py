import asyncio
from ai_agents.database_manager_agent import DatabaseManagerAgent
from ai_agents.product_sales_agent import ProductSalesAgent

async def main():
    test_scenario = 3

    if test_scenario == 1 or test_scenario == 3:
        # Create an instance of the database manager agent.
        db_agent = DatabaseManagerAgent()

        # Have the db agent create the database.
        create_db_result = await db_agent.run_task("Create the initial database to manage inventory.")
        print(create_db_result)

        # Have the db agent create the products table.
        create_products_table_result = await db_agent.run_task("Create the products table.")
        print(create_products_table_result)

        # Have the db agent add test data into the products table.
        populate_products_table_result = await db_agent.run_task("Add test data into the products table.")
        print(populate_products_table_result)

        # Have the db agent delete all rows from the products table.
        # delete_rows_from_products_table_result = asyncio.run(
        #     db_agent.run_task("Delete all rows from the products table.")
        # )
        # print(delete_rows_from_products_table_result)

    if test_scenario == 2 or test_scenario == 3:
        # Create an instance of the product sales agent.
        product_sales_agent = ProductSalesAgent()

        # Have the sales agent sell two computers.
        sell_products_result = await product_sales_agent.run_task("Sell 2 computers.")
        print(sell_products_result)

if __name__ == "__main__":
    asyncio.run(main())
