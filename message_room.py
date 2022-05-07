import requests
import sys
import json
import logging
from pathlib import Path
import rich_click as click
from rich import print_json
from rich.console import Console

# -------------------------
# Jinja2
# -------------------------

from jinja2 import Environment, FileSystemLoader
template_dir = 'Templates/'
env = Environment(loader=FileSystemLoader(template_dir))
template_dir = Path(__file__).resolve().parent

class GetJson():
    def __init__(self,
                roomid,
                token,
                title,
                description,
                location,
                date,
                time,
                speakers,
                url,
                url_label,
        ):
        self.roomid = roomid
        self.token = token
        self.title = title
        self.description = description
        self.location = location
        self.date = date
        self.time = time
        self.speakers = speakers
        self.url = url
        self.url_label = url_label

    def send_adaptive_card(self):
        webex_roomid = self.roomid
        webex_token =  self.token
        adaptive_card_template = env.get_template('generic_adaptive_card.j2')
        webex_adaptive_card = adaptive_card_template.render(roomid = webex_roomid,title=self.title,description=self.description,location=self.location,time=self.time,speakers=self.speakers,url=self.url,url_label=self.url_label)
        with open(f'{self.title}.json', 'w') as f:
            f.write(webex_adaptive_card)
        print(webex_adaptive_card)
        # send Adaptive Card to WebEx               
        webex_adaptive_card_response = requests.post('https://webexapis.com/v1/messages', data=webex_adaptive_card, headers={"Content-Type": "application/json", "Authorization": "Bearer %s" % webex_token })
        print('The POST to WebEx had a response code of ' + str(webex_adaptive_card_response.status_code) + 'due to' + webex_adaptive_card_response.reason)                
        click.secho(f"Following WebEx sent { sys.path[0] }/{self.title}.json",
            fg='green')

    # Create Testbed

@click.command()
@click.option('--roomid',
    prompt='Room ID',
    help='Type in the room ID to send the card to',
    required=True, envvar="ROOMID")
@click.option('--token',
    prompt='Room Token',
    help='Type in the room token to send the card to',
    required=True, envvar="TOKEN")    
@click.option('--title',
    prompt='Title of the Session',
    help='Main Title of the Session',
    required=True, envvar="TITLE")
@click.option('--description',
    prompt='Description of the Session',
    help='A Brief description of the session',
    required=True,
    envvar="DESCRIPTION")
@click.option('--location',
    prompt='Location',
    help='The Location of the Session',
    required=True,
    envvar="Location")
@click.option('--date',
    prompt=True,
    help="The Date of the Session",
    required=True,
    envvar="DATE")
@click.option('--time',
    prompt=True,
    help="The Time of the Session",
    required=True,
    envvar="TIME")
@click.option('--speakers',
    prompt='Speakers',
    help=('The Speakers Names of the Session'),
    required=True,
    envvar="SPEAKERS")
@click.option('--url',
    prompt='The URL to your session',
    help=('A URL for the speakers'),
    required=True,
    envvar="URL")
@click.option('--url_label',
    prompt='The Label on the URL to your session',
    help=('A Label for the URL for the speakers'),
    required=True,
    envvar="URL_LABEL")  
def cli(roomid,
        token,
        title,
        description,
        location,
        date,
        time,
        speakers,
        url,
        url_label,
        ):
    invoke_class = GetJson(roomid,
                            token,
                            title,
                            description,
                            location,
                            date,
                            time,
                            speakers,
                            url,
                            url_label,
                            )
    invoke_class.send_adaptive_card()

if __name__ == "__main__":
    cli()
