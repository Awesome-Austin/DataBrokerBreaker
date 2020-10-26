# Internet Data

Inspired by a reddit post from [r/youshouldknow](https://old.reddit.com/r/YouShouldKnow/comments/8tf6pq/ysk_that_online_databases_that_collect_your/) regarding Data Brokers (sites that aggregate personal data). 

The idea will be to have a CSV file consisting of a list of names (`names.csv` for example). This project will go through each line and go through the steps required the removal of data for the following sites:
* [BeenVerified](#BeenVerified)
* [FamilyTreeNow](#FamilyTreeNow)
* [Intelius](#Intelius)
* [MyLife](#MyLife)
* [Radaris](#Radaris)
* [Spokeo](#Spokeo)
* [WhitePages](#WhitePages)

Each site has different steps, but they are all set up to be as big of a pain in the ass as they can. As such, the code requires constant user interaction and can only submit a small number of requests at a time.
One might be able to get around this by using a VPN to change the IP address from which the requests are being made.

Some sites require that an email address be entered, to which they will send an email for the user to confirm that they are real.
If possible use a masked email; The emails are often delayed, so a temp email (ex: [10 minute mail](https://10minutemail.com/10MinuteMail/index.html)) may not allow for enough time (I refreshed one for an hour and no emails came in.).     

## Included Sites
### [BeenVerified](https://www.beenverified.com/)

<i>BeenVerified requires the use of an email address order to complete their opt-out process and remove your information from their database.</i>

#### Opt Out Steps
1) Go to their [opt-out page](https://www.beenverified.com/f/optout/search) and search for your listing by putting your first and last name.
0) Find for your listing and click on the arrow to the right of the box.
0) Enter your email address (we recommend using a masked email) and perform the CAPTCHA.
0) A confirmation email will be sent to you within a few minutes.
0) Click `verify opt-out` at the bottom of the email.
0) You will be redirected to their website.
0) You will receive a final confirmation email.
    
### [FamilyTreeNow](https://www.familytreenow.com)

#### Opt Out Steps
1) Go to the [opt-out page](https://www.familytreenow.com/optout/beginoptout).
0) perform the CAPTCHA at the bottom of the page.
0) Run a search.
0) Find yourself in the results, click on the record detail.
0) Click the red `Opt Out` button that is on the page.
0) Allow 48 hours for request to be processed.
    * Once processed the record will be removed from all places on the site.
* Note: If you have multiple records that need to be removed, repeat steps.
### [Intelius](https://www.intelius.com/)

<i>Intelius requires the use of an email address order to complete their opt-out process and remove your information from their database.</i>

#### Opt Out Steps
1) Go to their [opt-out page](http://intelius.com/optout) and search for your listing.
0) Find your listing and click `select and continue`.
0) Enter your email address (we recommend using a masked email), perform the CAPTCHA, and click `continue`.
0) You will be shown a page saying that a verification link was sent to your email.
0) Open your email and click on the verification link that was sent to you.
0) You will be redirected back to the Intelius page, confirming that your request was successfully submitted.
0) Next, you will get an email that your request is being processed.
0) Wait for the final confirmation email. You should get this within 72 hours.
               
### [MyLife](https://www.mylife.com/)

<i>MyLife requires the use of an email address order to complete their opt-out process and remove your information from their database.</i>

#### Opt Out Steps

0) Go to [mylife.com](https://www.mylife.com/) and search for your listing
0) Click `See Reputation Score`.
0) On the results page, click `See Background & Reputation Score`.
0) Copy and paste the url of your profile.
0) Compose an email to `removalrequests@mylife.com`.
    0) ask them to remove your profile (include the url from Step 3).

            MyLife Customer Service
            This is a request for all of my information to be removed from your site, and any affiliated sites.
            Here is the link to my profile: [link].
            Thank you,
            [Your Name]
0) Within a few minutes, you will get an email telling you that they have received your request and will fulfill it in 7-10 business days. 

#### If MyLife Still Refuses to Remove Your Info:
Email them at `privacy@mylife.com` using the following template:
        
        Hello,
        I am a vitim of stalking. I demand my Personal Identifiable information opted-out from your site and service, and all those you own.
        My information is as follows:
            * full_name
            * date_of_birth
            * street_address
            * city, state zip
        Signed,
        your_name

    
### [Radaris](https://radaris.com)

<i>Radaris requires the creation of an account on their website in order to complete their opt-out process and remove your information from their database.</i>

#### Opt Out Steps
1) Go to https://radaris.com/ and search for your listing.
0) Find it and click `Full Profile`.
0) Roll over the arrow next to `Background Check & Contact Info`, and click `Control Info`.
0) Click `Control Info` (it may say `Manage Info`).
0) Create an account (we recommend using a masked email) and perform the CAPTCHA.
0) Claim your profile by entering your cell phone number and entering the verification code.
0) Enter the verification code and click `Submit`.
0) Click `View my Account`.
0) Click `Delete Specific Records`.  <b><i>You may only delete 6 records.</i></b>
0) Select the records by checking the boxes and click `remove selected records`.  Go back to your account by clicking `back to [your name]'s page`.
0) Do steps 2-4 again to view your account, and click `make profile private`.
0) Your information should not be able to be seen anymore.
    
### [Spokeo](https://www.spokeo.com/)

<i>Spokeo requires the use of an email address order to complete their opt-out process and remove your information from their database.</i>

#### Opt Out Steps
0) Search for listing on [spokeo.com](https://www.spokeo.com/)
0) Find your listing and click on it to see your profile.
0) Copy the url of your profile.
0) Go to their opt-out website, [spokeo.com/optout](https://www.spokeo.com/optout).
0) Paste the url of your listing
0) Enter an email (we recommend using a masked email), and perform the CAPTCHA.
0) Click verification link sent to your email.
0) You will be redirected to a final confirmation page.
    
### [WhitePages](https://www.whitepages.com/)

<i>WhitePages requires the use of a phone number order to complete their opt-out process and remove your information from their database.</i>

#### Opt Out Steps
1) Go to whitepages.com. Type your name in the search box.
0) Find your listing and click `View Details`, and you'll be taken to your listing with your personal information.
0) Copy the URL of your page.
0) Go to their [opt-out page](https://www.whitepages.com/suppression_requests), and paste the URL to your listing.
0) Click the `Opt-out` button on this page.
0) The next page will ask you to confirm that this is your listing;  Click the `Remove me` button on this page.
0) They will then ask you why you want to opt out of Whitepages.  We like `“I just like to keep my information private”`.
0) Click `Submit`.
0) Type in your phone number, and they will give you a verification code to type on the next page.
0) Make sure you check the little box underneath.
0) Click `Call now to verify`
0) you’ll receive a robo-call asking for the verification code that pops up on the next screen.
0) When prompted, dial the verification code.
    * The robot will tell you that your opt-out request was accepted, and may take up to 24 hours for your profile to be removed from Whitepages.


    # TODO: find a webservice for the phone number.  
   
   
## Possible Future Sites


An extended list of Data Brokers can be found at the [Privacy Rights Clearinghouse](https://www.privacyrights.org/data-brokers) and in a [Vice Article](https://www.vice.com/en/article/ne9b3z/how-to-get-off-data-broker-and-people-search-sites)
