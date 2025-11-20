Feature: Todo App Management
  As a user
  I want to manage my todo items
  So that I can track my tasks
  
  Background:
    Given I navigate to "https://eviltester.github.io/simpletodolist/todo.html"
    And I wait 2 seconds for the page to load


  Scenario: Add a new todo item
    When I type the input field "Enter new todo text here" with text "Buy groceries" - hint: use browser_type tool
    And I press the "Enter" key
    Then I should see text "Buy groceries" on the page
    And the todo list should contain at least 1 item
