# Installation

Download or pull project off of github, code provided in the link below.  <br>
Runs on python 3.4 or greater, requires just the requests module; but it will need a valid CIBC username and password to run (mine have been removed for security reasons).
ScipyStack.py is a file of requirements for my general scipy stack, but not required for this project

---
**NOTE**

For the code, go to <a href="https://github.com/louismillette/Banking/tree/master">here</a>

---

# Getting Started

To begin, make a call to the StudentBanking function, providing monthly expense, real exclusion, and extra arguments.  When prompted, provide bank card number and password.

## Monthly expenses
Monthly expenses is a dictionary of expense names and values representing their costs, each being calculated monthly.  For example

      MonthlyExpenses={
              'laundry': 20,
              'groceries': 130,
              'phone': 40,
              'hydro': 60
      }
these items will be used to calculate weekly income, after expenses (weekly)

## Real Exclusion
Real exclusion is for banking items that you do not want included in the analysis.  For example

      realExclusion={
          'rent': [re.compile(r'PREAUTHORIZED DEBIT .* KW4RENT INC'),625, 2, 'Debit'],
                              r'PREAUTHORIZED DEBIT .* KW4RENT INC'
          'tuition': [re.compile(r'INTERNET BILL PAY .* UNIVERSITY OF WATERLOO'),3224.89,1,'Debit']
      }
these items are provided as a dictionary of lists, each list of 4 values: 

  * regex to find the description of the item in the list of banking transactions

  * amount of money this will exclude, each time

  * number of times to exclude this item

  * 'Debit' or 'Credit' transaction type

The total amount of money (lump sum) adds or subtracts the amount corresponding to the real exclusion, then the individual transactions are excluded from the rest of the analysis.  These transactions are included in the number amounts shown, but as if they all occurred at the beginning of the term instead of incrementally throughout the term.

## Extra

The extra argument allows you to compare the current term to prior terms.  It'll look something like this:

    extra=[
            {
                'name': 'Fall 2016',
                'dateFrom':datetime.datetime(year=2016,month=9,day=1),
                'dateUntil':datetime.datetime(year=2016,month=12,day=20),
                'MonthlyExpenses':MonthlyExpenses,
                'customExclusions':{
                        'rent': [re.compile(r'PREAUTHORIZED DEBIT .* KW4RENT INC'), 625, 4, 'Debit'],
                        'tuition': [re.compile(r'INTERNET BILL PAY .* UNIVERSITY OF WATERLOO'),2550.25, 1,'Debit']
                }
            },
            {
                'name': 'Spring, 2016',
                'dateFrom':datetime.datetime(year=2016,month=5,day=1),
                'dateUntil':datetime.datetime(year=2016,month=8,day=20),
                'MonthlyExpenses':MonthlyExpenses,
                'customExclusions':{
                    'rent': [re.compile(r'PREAUTHORIZED DEBIT .* KW4RENT INC'), 625, 4, 'Debit'],
                    'tuition': [re.compile(r'INTERNET BILL PAY .* UNIVERSITY OF WATERLOO'),2445.19, 1, 'Debit']
                }
            },
            {
                'name': 'Winter, 2015',
                'dateFrom':datetime.datetime(year=2015,month=1,day=1),
                'dateUntil':datetime.datetime(year=2015,month=4,day=20),
                'MonthlyExpenses':MonthlyExpenses,
                'customExclusions':{
                    'rent': [re.compile(r'.* ZAIN VALANI'), 560, 3, 'Debit'],
                    'tuition': [re.compile(r'INTERNET BILL PAY .* UNIVERSITY OF WATERLOO'), 1049.0, 1, 'Debit']
                }
            },
        ]

extra takes a list of dictionaries, each representing a period, given by dateFrom and dateUntil (python datetimes), using custom exclusions and month expenses explained above, and a name for the chart

# Template
 
 It is important to maintain the original directory structure before running.  After running program template.html in the bankingTemplate directory will have been updated, to reflect the arguments provided to the StudentBanking function. 

 The template treats all credit to the account as a lump sum payment at the beginning of the term, even if that is not the case, and pulls from that lump sum the grand total of all the real exclusions as if they had happened at the beginning of the term, even if that is not the case.  Real Exclusions are then ignored from the statement moving forward.  

  * `Balance` is the lump sum less any debits to the account, excluding the real exclusions
  * `Income` is represented by dividing the current amount left in the lump sum by the remaining number of weeks, for each week
  * `Income After Bills` is that weeks income, less the weekly bills (provided by month, calculated for each week)
  * `Expenditure` is the sum of the debits, excluding real exclusions, pulled from the CIBC API for each given week

