# 🎈 Djisco - DIY event organiser 🎈

Djisco is a web application which allows users to organise events.  It is built using Django and it is currently being actively developed.

## Current Features ✅

- Create and attend events 
- View created events in the past and future
- Request attendees bring specific items to the event (for instance food, sound equipment)
- As an attendee, commit to fulfilling event requirements and bringing items
- Users can view a list of events they are attending as well as their commitments for each event


## Future Features ⏰

Djisco is still in development.  Here is a roadmap of features that I intend to implement, in approximate priority order.

- Allow users to add each other as "friends"
- Allow users to invite each other to events
- A volunteering system, where organisers can request specific jobs for a given event (e.g. bar / door work for the event) and attendees can commit to fulfilling those roles
- A ticketing system for events 
- A calendar interface, showing the user events they are attending


### What now?

I'm currently working on getting the web app to an MVP level.  Key changes before MVP level is reached:

- Events search - Add a search bar to list view
- Improved locations - Use actual locations for events and implement a map and distance search
- Invites - Allow users to invite other users to events
- Calendar Integration - Users who RSVP can add events to their chosen callendar app
- Social Media Sharing - Allow users to share events on various platforms
- Event analytics - Enhanced detail view tab for organisers showing, for example, RSVPs over time.

## Running Djisco on your machine 🌞

Clone this repository and navigate to the base directory. Ensure you are using a Python environment with the project requirements installed (requirements.txt). Run:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

You should now be able to use the app locally at localhost:8000. 

  
