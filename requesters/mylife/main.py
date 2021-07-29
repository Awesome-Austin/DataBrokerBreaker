from requesters.abstract.main import send_message


def mylife_request(mylife_record):
    """

    :param mylife_record: pd.Series for the record.
    :return:
    """

    # send_to = "privacy@mylife.com"
    send_to = "aus.gifford@gmail.com"
    subject = f"Question regarding site record number {mylife_record.id}"
    message_text = f"""
    To whom it may concern:
        I found myself on your website, and due to personal safety concerns need to have it removed.
        The record in question is {mylife_record.id}, which I found at the URL <{mylife_record.url}>
        
        I am aware that your site gathers data from other sources: Would you be able to send me the locations from 
        which the data was gathered?
        
        Thank you,
        {mylife_record.givenName} {mylife_record.familyName}
    """
    send_message(send_to, subject, message_text)


if __name__ == '__main__':
    import pandas as pd
    records = pd.read_csv(
        r"C:\Users\nk3737\PycharmProjects\DataBrokerBreaker\files\output\Gifford_Austin\MyLife_2020-12-07.csv"
    )
    for id, record in records.iterrows():
        mylife_request(record)
