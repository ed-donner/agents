Feature: Todo App Management
  As a user
  I want to manage my todo items
  So that I can track my tasks

  Scenario: Add a new todo item
    Given I navigate to "https://eviltester.github.io/simpletodolist/todo.html"
    When I type the input field "Enter new todo text here" with text "Buy groceries" - hint: use browser_type tool
    And I press the "Enter" key
    Then I should see text "Buy groceries" on the page
    And the todo list should contain at least 1 item

  Scenario: Add multiple todos
    Given I navigate to "https://eviltester.github.io/simpletodolist/todo.html"
    When I add todo "First task"
    And I add todo "Second task"
    Then I should see text "First task" on the page
    And I should see text "Second task" on the page