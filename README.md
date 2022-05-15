# Timed Alert
Timed Alert is a minimal alarm solution. Using configs, you can set different alarms and schedules in a breeze!

## Installation
Clone the repository. Run `pip install -r requirements.txt` to install the dependencies.

## Usage
```
python main.py
```

By default, it uses `config.ini`. You may use other configs with it using the `-c` or the `--config` flag
```
python main.py -c {path/to/config}
```

Configs must comply with the INI file format. The `Settings` section can be omitted
