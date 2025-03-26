```markdown
# Hue Colour Setter

This project provides a tool to automate the color and brightness settings of Philips Hue lights based on messages received from a NATS streaming server. The application listens for color settings streamed via NATS and then controls specified Hue lights accordingly.

## Features

- Connects to a Philips Hue Bridge to control lights.
- Listens to a NATS streaming server to receive color change requests.
- Converts color from HEX to Philips Hue's hue-saturation-brightness format.
- Sets light color and brightness based on received messages.

## Requirements

- Python 3.6+
- Philips Hue Bridge and compatible lights.
- NATS server for streaming messages.
  
## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/hue-colour-setter.git
   cd hue-colour-setter
   ```

2. **Install dependencies:**

   Make sure you have `pip` installed in your Python environment.

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment:**

   Ensure that your Hue Bridge username and access token are set. The script expects a JSON file located at `~/.hue-tokens.json` to load the access token:

   ```json
   {
       "access_token": "YOUR_ACCESS_TOKEN",
       "refresh_token": "YOUR_REFRESH_TOKEN"
   }
   ```

   Also, set your Hue Bridge username in the environment as `HUE_USERNAME`.

4. **Configure the NATS server:**

   If you are using a custom NATS server, ensure the environment variable `NATS_SERVER` is set to the correct URL (e.g., `nats://your-nats-server:4222`).

## Usage

To run the script, use the following command:

```bash
./hue-set.py --username YOUR_HUE_USERNAME
```

You can also use additional command-line options:

- `--nats-server`: Specify the URL of the NATS server.
- `--nats-alert-colours-stream`: Specify the NATS stream name to subscribe to.
- `--tokens-file`: Path to the file containing the Hue access token.
- `--device-name`: The name of the Hue light device you want to control.
- `--debug`: Enable debug logging for more verbose output.

## Example

```bash
./hue-set.py --username your_username --nats-server nats://localhost:4222 --device-name LivingRoomLight --debug
```

## License

This project is licensed under the MIT License.
```

