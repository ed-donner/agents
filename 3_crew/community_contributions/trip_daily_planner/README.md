# Trip Daily Planner with Traveler's Information Input and Email Sending Tool

### It has following features:

* The application will get traveler's necessary information: destination, flight, hotel location, trip duration, personal interests, dining restrictions and preferences and email from Gradio UI. The application will plan daily activities and restaurants for the trip and send daily planner to the email provided.  For example, if I have personal interests as
  `Enjoy historic and cultural sites. An out-of-town day trip is fine. Include biking activities in one of days`
  It will plan a bike ride and out-of-town day trip for me. It will honor dining retrictions or preferences too.
  It was originally inspired by [CrewAI's surprise trip example](https://github.com/crewAIInc/crewAI-examples/tree/main/crews/surprise_trip) with additions of 'personal interests' and 'dining restrictions and preferences' plus Gradio UI and sending email tool/ agent/ task additions.
* The crew has 4 agents: personalized_activity_planner, restaurant_scout, itinerary_compiler and email_agent and 4 tasks:
  personalized_activity_planning_task, restaurant_location_scout_task, itinerary_compilation_task and format_send_email_task
  'itinerary_compiler' will gather info from 'personalized_activity_planner' and 'restaurant_scout' and compile into strictured pydantic output of Itinerary and email agent will reformat into HTML, subject line and send  email accordingly.

### Lessons Learned:

* I ran into rate limit error right away regardless of using OpenAI or Claude as LLMs.  Both have 30,000 tokens per minute rate limit.  I get it working with the following Agent and SerperDevTool parameters. The most important parameter is SerperDevTool's n_results that decides numbers of tokens parsed in one run. It fails right away if I bump it up to 5.

  Agent(
  config=self.agents_config['personalized_activity_planner'],
  tools=[SerperDevTool(n_results=3), ScrapeWebsiteTool()],
  max_retry_limit=1,
  max_iter=2,
  respect_context_window=True,
  verbose=True,
  allow_delegation=False,
  )
* One advantage of using CrewAI is that it templatizes parameters so that destination, flight, hotel location, trip_duration, personal_interests, dining_restrictions_preferences and email are all passing as individual template variables rather than mushed together as an agent's user prompt. One disadvantage of CrewAI is that individual task completion is invisible.  Therefore, I cannot display the progress in UI.  I cannot get the final output of individual task either.
* The Gradio deployment is not as straight-forwarded. Yes, you need to deploy from the crew project root and include 'crewai' and 'crewai_tools' as dependencies. Also main.py references crew.py as '{project}.crew' like
  'from trip_daily_planner.crew import TripDailyPlanner' when we create crewai using 'crewai create crew trip_daily_planner'. That absolute reference from crew project root won't work. It can only reference each other using relative path like 'from crew import TripDailyPlanner' instead.

### Github Codes:

https://github.com/threecuptea/agents

### The demo:

https://huggingface.co/spaces/threecuptea/trip_daily_planner
