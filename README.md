
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/9150d466141e47abaa12d0d55c2c57a9/badge.svg)](https://www.quantifiedcode.com/app/project/9150d466141e47abaa12d0d55c2c57a9)

A RESTful API written in Django for lookup of colorado property data


## Setting up
This project was built with python +3.4

```bash
$ virtualenv -p python3 env
$ source ./env/bin/activate
$ pip install -r requirements.txt
$ cd coprop
$ python manage.py migrate --settings=coprop.settings_development
$ python manage.py runserver  --settings=coprop.settings_development
```

Then head to http://localhost:8000/api/v1/ in your browser to get started.

username: admin
password: test1234

### Definitions regarding tax liens:

* Owner: The owner of the Parcel. Example: [SMITH, SHANNON MARIE owner of parcel R010100](http://assessor.co.grand.co.us/assessor/taxweb/account.jsp?accountNum=R010100)
* Tax: tax owed to the county for a property for a given tax year. Example [Tax charge of $967.24 for tax year 2015](https://ecomm.co.grand.co.us/treasurer/treasurerweb/account.jsp?account=R010100&action=tx)
* Lien holder: the person or company that purchased the tax lien from the county at auction.
* Tax Lien or Lien: The right to possess a property belonging to another person until a debt owed by that person is discharged. For a tax lien possess does not nessasarily happen but could. The loen hold earns interest on the debt.
* Lien sale price, Lien premium: Unpaid tax is sold as a lien. The lien is sold at auction, starting price is the tax owed. The Lien premium is the amount paid more than the tax. For example: Parcel R300935 had unpaid tax for 2012. The tax amount was (tax year = 2012,	Tax Charge	on 1/1/13	$1,145.20) The lien sold at auction (tax year = 2012,	Lien sold	11/7/13	$1,249.36) 1249.36-1145.20 = 104.16, 104.16 is the premium. [data from here](https://ecomm.co.grand.co.us/treasurer/treasurerweb/account.jsp?account=R300935&action=tx)
