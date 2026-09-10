# Project wants

## High level wants

I want this to be a project where I can run it locally, and it will help me keep track of the work that I need to do every day.
A big part of what I do is monitoring:
- Slack messages that come into the error monitoring channel.
  - The messages that come into the error monitoring channel may be multiple messages representing a single Sentry issue. I need to have those consolidated into a single item that I can view to see all the occurrences of it and what the current status of work against it is. That way, I can keep notes on whether this is something where I'm creating a ticket and archiving it, or if I need somebody else to look into it. 
- Messages that come into our team support channel.
- Open PRs that are tagged with the label ops at least once a day.
- To-dos that are in Notion that I need to make sure that I follow up on.
- Incidents in Incident.IO that may need work to clean up their timeline, create the postmortem document, or schedule a review.
- Calendar events on multiple Google calendars that I should be aware of at a glance.

## Technology criteria

Running locally, I should have some sort of persistence so that I can shut off the system at night, turn it back on in the morning, and see where I left off. I'm not overly concerned with disaster recovery or backups, but if we can come up with a lightweight way of doing that, then we can leverage, for example, my NAS that is on the same network.

## Known limitations

I don't know if I have the ability to use an API key against Slack. I do have Claude Code able to use the Slack MCP to look at messages, but that seems like overkill for periodic polling.