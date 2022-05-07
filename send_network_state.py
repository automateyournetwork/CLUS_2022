import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import sys
import json
import logging
from pathlib import Path
from pyats.topology import Testbed, Device
from genie import testbed
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
                hostname,
                os,
                username,
                password,
                command,
        ):
        self.roomid = roomid
        self.token = token
        self.hostname = hostname
        self.os = os
        self.username = username
        self.password = password
        self.command = command
        if self.os == "nxos":
            self.supported_templates = [
                "platform",
            ]
        else:
            self.supported_templates = [
                            'platform',
]

    def send_adaptive_card(self):
        for single_command in self.supported_templates:
            self.command = single_command
            parsed_json = json.dumps(self.capture_state(), indent=4, sort_keys=True)
            #print_json(parsed_json)
            if "Cannot" in parsed_json:
                click.secho("No Data To Create File", fg='red')
            else:
                self.template_network_state_apartive_card(parsed_json)

    def template_network_state_apartive_card(self, parsed_json):
        webex_roomid = self.roomid
        webex_token =  self.token
        for template in self.supported_templates:
            if self.command == template:
                adaptive_card_template = env.get_template(f'{self.os}_adaptive_card.j2')
                webex_adaptive_card = adaptive_card_template.render(command = self.command, to_parse_platform=json.loads(parsed_json),roomid = webex_roomid,device_id = self.hostname)                   
                with open(f'{self.hostname} {self.command}.json', 'w') as f:
                    f.write(webex_adaptive_card)
                print(webex_adaptive_card)
                # send Adaptive Card to WebEx               
                webex_adaptive_card_response = requests.post('https://webexapis.com/v1/messages', data=webex_adaptive_card, headers={"Content-Type": "application/json", "Authorization": "Bearer %s" % webex_token })
                print('The POST to WebEx had a response code of ' + str(webex_adaptive_card_response.status_code) + 'due to' + webex_adaptive_card_response.reason)                
                break
            else:
                click.secho(f"Following command not supported {self.command}", fg='red')
        click.secho(f"Following WebEx sent { sys.path[0] }/{self.hostname} {self.command}.json",
            fg='green')

    # Create Testbed
    def connect_device(self):
        try:
            first_testbed = Testbed('dynamicallyCreatedTestbed')
            testbed_device = Device(self.hostname,
                        alias = self.hostname,
                        type = 'switch',
                        os = self.os,
                        credentials = {
                            'default': {
                                'username': self.username,
                                'password': self.password,
                            }
                        },
                        connections = {
                            'cli': {
                                'protocol': 'ssh',
                                'ip': self.hostname,
                                'port': 22,
                                'arguements': {
                                    'connection_timeout': 360
                                }
                            }
                        })
            testbed_device.testbed = first_testbed
            new_testbed = testbed.load(first_testbed)
        except Exception as e:
            logging.exception(e)
        return new_testbed

    def capture_state(self):
        # ---------------------------------------
        # Loop over devices
        # ---------------------------------------
        for device in self.connect_device():
            device.connect(learn_hostname=True,log_stdout=False)
        # Parse or Learn based on command
            if 'show' in self.command:
                try:
                    command_output = device.parse(self.command)
                except:
                    command_output = f"Cannot Parse { self.command }"
            elif self.command == "config":
                try:
                    command_output = device.learn(self.command)
                except:
                    command_output = f"Cannot Parse { self.command }"
            elif self.command == "platform":
                try:
                    command_output = device.learn(self.command).to_dict()
                except:
                    command_output = f"Cannot Parse { self.command }"
            else:
                try:
                    command_output = device.learn(self.command).info
                except:
                    command_output = f"Cannot Parse { self.command }"
            device.disconnect()
            return command_output

@click.command()
@click.option('--roomid',
    prompt='Room ID',
    help='Type in the room ID to send the card to',
    required=True, envvar="ROOMID")
@click.option('--token',
    prompt='Room Token',
    help='Type in the room token to send the card to',
    required=True, envvar="TOKEN")    
@click.option('--hostname',
    prompt='Hostname',
    help='Hostname of device - must match the device',
    required=True, envvar="HOSTNAME")
@click.option('--os',
    prompt='OS',
    type=click.Choice(['ios', 'iosxe', 'iosxr', 'nxos'],
        case_sensitive=True),
    help='OS of device - must match the device',
    required=True,
    envvar="OS")
@click.option('--username',
    prompt='Username',
    help='Username',
    required=True,
    envvar="USERNAME")
@click.option('--password',
    prompt=True,
    hide_input=True,
    help="User Password",
    required=True,
    envvar="PASSWORD")
@click.option('--command',
    prompt='Command',
    help=('''A valid pyATS Learn Function (i.e. ospf)
             or valid CLI Show Command (i.e. "show ip interface brief")'''),
    required=True)

def cli(roomid,
        token,
        hostname,
        os,
        username,
        password,
        command,
        ):
    invoke_class = GetJson(roomid,
                            token,
                            hostname,
                            os,
                            username,
                            password,
                            command,)
    invoke_class.send_adaptive_card()

if __name__ == "__main__":
    cli()
