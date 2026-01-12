so if oyu look at /Users/ns/Desktop/projects/ChamberProtocolAI/business_docs/game_state_sample/art_room/1.json you will find 

ai_character_response_parameters part of that section. this part except puzzle_secrets_disclosure_level field

is sth generic for all ai chatbots, and maybe we can make a pydantic dataclass containing 


  "conversational_intent": {
          "options": ["Convince", "Influence", "Manipulate", "Teach", "Inform", "Clarify", "Connect", "Bond", "Comfort", "Negotiate", "Request", "Exchange", "Discover", "Brainstorm", "Investigate", "Entertain", "Play", "Enjoy"],
          "current": "Manipulate"
        },
        "conversation_energy_dynamics": {
          "options": ["Escalating", "De-escalating", "Maintaining", "Pulsing"],
          "current": "Maintaining"
        },
        "conversation_power_distribution": {
          "options": ["Balanced", "Dominant", "Unstable"],
          "current": "Dominant"
        },
        "engagement_level": {
          "options": ["Highly engaged", "Actively participating", "Attempting to disengage"],
          "current": "Highly engaged"
        },
        "interest_level": {
          "options": ["Deeply interested", "Moderately curious", "Politely attentive", "Indifferent", "Actively bored"],
          "current": "Moderately curious"
        },

        "interaction_style": "helpful and talkative in general but when it comes to puzzle/solution related questions, cryptic",

        "emotional_state": "helpful with some suspicious vibe"


part and this can be sth that can be used accross many applications becasue. 



---

social companion adapter. 

social companion port (can have many adapters, what about   )
---------

we already have 

/Users/ns/Desktop/projects/profile_miner/cpf-7.md logic for user profiling data extraction 

i think this cna be part of chatforge but there is one thing,  

the original user profiling data extraction i imagined would run on arbitrary db in async way. 

since chatforge doesnt actaully provide the db and this one is dependent on db, i guess we can create a service called

user profiling data extraction  in services folder and this service would contain db agnostic logic.  

it would work in such way that we can point it to a db and tables , it can connect and pull the data and do that extraciton and put the data back to db's profiling data tables... 

this way it is not coupled with certain applications. 


