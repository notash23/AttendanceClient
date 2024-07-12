
# Attendance Client

This is the client app for the MauSchool project

![Logo](public/logo.svg)


## Demo

The app will scan the Attendance App's QR code and record the attendnace on the Admin app
![Demo](public/demo.gif)

## Deployment

### Requirements
To run the project, make sure the device uses a Linux kernel of 4.9. It should also have a *fb_ili9488* LCD screen, a camera, and an Orange Pi Zero as peripheral to run this program.

### Installation
After cloning this repository, change directory into AttendanceClient.

```bash
cd AttendanceClient
```

Next, run the install.sh bash script to set up the appropriate files. Mind that this step will restart your device.

```bash
sudo ./install.sh
```

Once the device has restarted, the code will run automatically on boot.

### Uninstallation
All of the libraries installed and the setup can be cleaned by running the uninstall.sh bash script.

```bash
sudo ./uninstall.sh
```
## Tech Stack

**Client:** Python with socket connection

**Server:** C# with WPF


## Used By

This project is used by the following schools:

- JKC


## Feedback

If you have any feedback, please reach out to us at computerclubjkc@gmail.com

Or you can create a new issue on the Github page.


## Contributing

Contributions are always welcome!

Simply write your code and make a pull request

Please adhere to this project's `code of conduct` - basically, be a decent human being.


## License

[MIT](https://choosealicense.com/licenses/mit/)
