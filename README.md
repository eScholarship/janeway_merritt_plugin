# Janeway Merritt Plugin

A plugin for [Janeway](https://janeway.systems/), enables preservation of preprint in Merritt upon preprint acceptance to a Janeway repository.

The plugin is triggered by the `preprint_publication` event. This event happens immediately after the button to send an acceptance e-mail is clicked.

## Installation

1. Clone this repo into /path/to/janeway/src/plugins/
2. run `python src/manage.py install_plugins`
3. Restart your server (Apache, Passenger, etc).
4. configure the plugin (see below)

## Configuration


Each preprint repository needs to have an associated Merritt Repo Settings object.

1. Navigate to admin and find the "Merritt" section
2. Click "Add" Repo Merritt settings
3. Select the appropriate repository and fill in the collection and other metadata
4. Save

## Usage

### Preprints 

When installed and configured, the plugin will send preprint to Merritt on publication. Result of sending zip and the callback is tracked.


## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## License

[BSD 3-Clause](LICENSE)
