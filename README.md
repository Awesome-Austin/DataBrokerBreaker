# Internet Data

Inspired by a reddit post from [r/youshouldknow](https://old.reddit.com/r/YouShouldKnow/comments/8tf6pq/ysk_that_online_databases_that_collect_your/) regarding Data Brokers (sites that aggregate personal data). 

The idea will be to have a CSV file consisting of a list of names (`names.csv` for example). This project will go through each line and go through the steps required the removal of data for the following sites:
* [Spokeo](#Spokeo)
* [MyLife](#MyLife)
* [Radaris](#Radaris)
* [WhitePages](#WhitePages)
* [Intelius](#Intelius)
* [BeenVerified](#BeenVerified)
* [FamilyTreeNow](#FamilyTreeNow)

Each site has different steps, but they are all set up to be as big of a pain in the ass as they can. As such, the code requires constant user interaction and can only submit a small number of requests at a time.
One might be able to get around this by using a VPN to change the IP address from which the requests are being made.

Some sites require that an email address be entered, to which they will send an email for the user to confirm that they are real.
If possible use a masked email; The emails are often delayed, so a temp email (ex: [10 minute mail](https://10minutemail.com/10MinuteMail/index.html)) may not allow for enough time (I refreshed one for an hour and no emails came in.).     

## Included Sites

### [Spokeo](https://www.spokeo.com/)
    # TODO: Write this section once the py file is created 

### [MyLife](https://www.mylife.com/)
    # TODO: Write this section once the py file is created
    
### [Radaris](https://radaris.com)
    # TODO: Write this section once the py file is created
    
### [WhitePages](https://www.whitepages.com/)
    # TODO: Write this section once the py file is created
    
### [Intelius](https://www.intelius.com/)
    # TODO: Write this section once the py file is created
    
### [BeenVerified](https://www.beenverified.com/)
    # TODO: Write this section once the py file is created
    
### [FamilyTreeNow](https://www.familytreenow.com)
    # TODO: Write this section once the py file is created

## Future Sites
An extended list of Data Brokers can be found at the [Privacy Rights Clearinghouse](https://www.privacyrights.org/data-brokers)