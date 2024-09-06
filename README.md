**Data loggers and Controller for the FrSky Imax B6 Mini Charger.**

The python files here provide three separate main modules and several
supporting modules to monitor and/or control the FrSky Imax B6 mini.

Be aware that there has been confusion regarding the output ports of the
Imax B6 and the Imax B6 mini chargers. The former uses some sort of
rs232/UART port and the latter uses a micro USB port as output. The
applications developed here strictly apply to the FrSky Imax B6 mini
with a USB port.

All the modules are contained within this one repository. The main
operating modules are: imax\_usb.py, imax\_logger.py, and run\_imax.py.
All somehow show Imax charging/discharging data in real-time.

imax\_usb.py is a basic logger adaptation, with only the console as the
interface, and output displayed to the console and ultimately output to
a .csv file.

imax\_logger.py is a big step up to your default browser based interface
to start/stop and graphically display the data. Output is to an .xlsx
file.

run\_imax.py builds on the latter, and both logs and controls the Imax
B6 mini. It adds nearly full control, saves your favorite Imax settings
for different or the same battery as reloadable programs, and ultimately
allows output of the charge/discharge data to .xlsx files.

All the work here was developed using an FrSky Imax B6 mini under
Windows 10 and with Python 3.6.1. Whether the applications will work
with other Imax knock-offs or under other operating systems is unknown.
The application should work with any python \> 3.x.x versions, provided
the appropriate libraries and packages have been installed.

**Note!** For Linux users, to run this script under non-root user install udev rules:

```shell
$ sudo install --mode=0644 --target-directory=/etc/udev/rules.d/ udev/90-smart-charger.rules
$ sudo udevadm trigger
```

See the imax\_B6\_mini\_log\_and\_control.docx MS Word file for details
on operation of the applications. The last section of the Word file also
contains all the relevant host to Imax and Imax to host relevant packet
descriptions. The format of the section is a detailed tutorial,
describing how the data was obtained and analyzed for those who wish to
develop their own code, or wish to extend, or fix the current codes.
There is also a pdf file, in case you have no way to open the .docx file
is available.

If a clone can use the FrSky Chargemaster software, then it will likely
directly work with the applications here. If not, the last section will
be useful to show you how to develop the appropriate information.
