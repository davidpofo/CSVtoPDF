import os
import sys
import re
import csv
from fdfgen import forge_fdf

sys.path.insert(0, os.getcwd())
tmp_file = "tmp.fdf"
output_folder = './output/'

def process_csv(file):
    headers = []
    data =  []
    csv_data = csv.reader(open(file))
    csv_data=list(csv_data)
    for i, row in enumerate(csv_data):
        if i == 0:
          headers = row
          continue
        field = []
        for i in range(len(headers)):
            field.append((headers[i], row[i]))
        data.append(field)
    return data

def form_fill(fields, row_count):
  fdf = forge_fdf("",fields,[],[],[])
  fdf_file = open(tmp_file,"wb")
  fdf_file.write(fdf)
  fdf_file.close()
  # fill in with borrower last name if there is something there or it uses Demo
  filename_prefix = fields[19][1] + "_" if fields[19][1] else "Demo "
  output_file = '{0}{1}{2}.pdf'.format(output_folder, filename_prefix, fields[1][1].replace(" ", "_"))
  if os.path.isfile(output_file):
      while True:
          new_file_name = '{0}{1}{2}_{3}.pdf'.format(output_folder, filename_prefix, fields[1][1].replace(" ", "_"), row_count)
          if os.path.isfile(f'{new_file_name}'):
              row_count += 1
          else:
              output_file = new_file_name
              break
  print(output_file)

  cmd = 'pdftk "{0}" fill_form "{1}" output "{2}" dont_ask'.format(pdffilename, tmp_file, output_file)
  os.system(cmd)
  os.remove(tmp_file)

def zipcheck(zipcode):
    if len(zipcode) == 5 and zipcode[0] != "0":
        return zipcode
    else:
        return "0" + zipcode

# argument for pdf file name
#pdffilename = 'example.pdf'
pdffilename = sys.argv[1]

# argument for hubspot form csv data filename
#hubspot_csv_filename = 'hubspot-form-submissions-sba-s-paycheck-protection-progr-2020-04-28.csv'
hubspot_csv_filename = sys.argv[2]

##1 read the hubform csv
data = process_csv(hubspot_csv_filename)
print('Generating Forms:')
print('-----------------------')
row_count = 0

for row in list(data):
    datalist = list(row)

    Full_Business_Address = ""
    Bottom_Business_Address = ""
    full_name = ""
    select_dict = {"Sole proprietor":"Off","Partnership":"Off","CCorp":"Off","SCorp":"Off","LLC":"Off","Independent contractor":"Off","501c3 nonprofit":"Off","Tribal business sec 31b2C of Small Business Act":"Off","Eligible selfemployed individual":"Off","501c19 veterans organization":"Off","Other":"Off"}
    purpose_dict = {"Payroll":"Off","Lease":"Off","Utilities":"Off","Other":"Off","Other explain":"None"}
    for index, item in enumerate(datalist):
        itemlist = list(item)
        if itemlist[0] == 'Legal Business Structure':
            if 'Sole' in itemlist[1]:
                select_dict['Sole proprietor'] = 'On'
            if 'Partnership' in itemlist[1]:
                select_dict['Partnership'] = 'On'
            if 'C-Corp' in itemlist[1]:
                select_dict['CCorp'] = 'On'
            if 'S-Corp' in itemlist[1]:
                select_dict['SCorp'] = 'On'
            if 'LLC' in itemlist[1]:
                select_dict['LLC'] = 'On'
            if 'Independent contractor' in itemlist[1]:
                select_dict['Independent contractor'] = 'On'
            if '501(c)(3) nonprofit' in itemlist[1]:
                select_dict['501c3 nonprofit'] = 'On'
            if 'Tribal business sec 31b2C of Small Business Act' in itemlist[1]:
                select_dict['Tribal business sec 31b2C of Small Business Act'] = 'On'
            if 'Eligible self-employed individual' in itemlist[1]:
                select_dict['Eligible selfemployed individual'] = 'On'
            if '501(c)(19) veterans organization' in itemlist[1]:
                select_dict['501c19 veterans organization'] = 'On'
            if 'Other' in itemlist[1]:
                select_dict['Other'] = 'On'

        # DBA
        if itemlist[0] == 'Doing Business As (DBA)':
            itemlist[0] = 'Text12'

        # Business name and address
        if itemlist[0] == 'Business Legal Name':
            itemlist[0] = 'Business Legal NameRow1'
        if itemlist[0] == 'Business Street Address':
            Full_Business_Address += itemlist[1]
            itemlist[0] = "Business AddressRow1"
        if itemlist[0] == 'Business City':
            Full_Business_Address += ' ' + itemlist[1] + ', '
            Bottom_Business_Address += itemlist[1] + ', '
        if itemlist[0] == 'Business State':
            Full_Business_Address += itemlist[1] + ' '
            Bottom_Business_Address += itemlist[1] + ' '
        if itemlist[0] == 'Business Zip Code':
            Full_Business_Address += zipcheck(itemlist[1])
            Bottom_Business_Address += zipcheck(itemlist[1])
            datalist.append(("Business AddressRow2", Bottom_Business_Address))
            datalist.append(("Text6", Full_Business_Address))
        if itemlist[0] == "Business EIN# (Tax ID Number)":
            itemlist[0] = 'Business TIN EIN SSNRow1'
        if itemlist[0] == "Business Phone Number":
            # Clean up Phone number
            phone_number = itemlist[1]
            clean_phone_number = re.sub('[^0-9]+', '', phone_number) # remove the series line number
            formatted_phone_number = re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1 ", "%d" % float(clean_phone_number[:-1])) + clean_phone_number[-1]
            datalist.append(("fill_12", formatted_phone_number))

        if itemlist[0] == 'Primary Contact Name':
            itemlist[0] = 'Primary ContactRow1'
        if itemlist[0] == 'Email Address':
            itemlist[0] = 'Email AddressRow1'
        if itemlist[0] == 'Number of Employees':
            itemlist[0] = 'Number of Employees as of 02/15/2020'

        # Average Monthly Payroll
        if itemlist[0] == 'Average Monthly Payroll':
            itemlist[0] = 'fill_14'

        # make purpose of loan columns based on what is in the purpose of loan column
        if itemlist[0] == 'Purpose Of Loan':
            if 'Payroll' in itemlist[1]:
                select_dict['Business Payroll / Salaries'] = 'Yes'
            if 'Lease' in itemlist[1]:
                select_dict['Business Rent'] = 'Yes'
            if 'Utilities' in itemlist[1]:
                select_dict['Business Utilities'] = 'Yes'
            if 'Other' in itemlist[1]:
                select_dict['Other'] = 'Yes'
                select_dict['Other explain'] = itemlist[1].split('Other')[-1].strip().replace(",","")

        # Applicant ownership Borrower First Name
        if itemlist[0] == 'Borrower Last Name':
            itemlist[0] = 'Last name'
            full_name += " " + itemlist[1]
        if itemlist[0] == 'Borrower First Name':
            itemlist[0] = 'First name'
            full_name += itemlist[1] + full_name

        # Title
        if itemlist[0] == 'Title':
            title = itemlist[1]
        # Ownership
        if itemlist[0] == 'Ownership %':
            itemlist[0] = 'Ownership 1'

        # Eight Check Boxes
        if itemlist[0] == '1) Is the Applicant or any owner of the Applicant presently suspended, debarred, proposed for debarment, declared ineligible, voluntarily excluded from participation in this transaction by any Federal department or agency, or presently involved in any bankruptcy?':
            if itemlist[1] == 'Yes':
                itemlist[0] = "Check Box19"
            else:
                itemlist[0] = "Check Box20"
                itemlist[1] = "Yes"
        if itemlist[0] == '2) Has the Applicant, any owner of the Applicant, or any business owned or controlled by any of them, ever obtained a direct or guaranteed loan from SBA or any other Federal agency that is currently delinquent or has defaulted in the last 7 years and caused a loss to the government?':
            if itemlist[1] == 'Yes':
                itemlist[0] = "Check Box21"
            else:
                itemlist[0] = "Check Box22"
                itemlist[1] = "Yes"
        if itemlist[0] == '3) Is the Applicant or any owner of the Applicant an owner of any other business, or have common management with, any other business? If yes, list all such businesses and describe the relationship on a separate sheet identified as Addendum A.':
            if itemlist[1] == 'Yes':
                itemlist[0] = "Check Box23"
            else:
                itemlist[0] = "Check Box24"
                itemlist[1] = "Yes"
        if itemlist[0] == '4) Has the Applicant received an SBA Economic Injury Disaster Loan between January 31, 2020 and April 3, 2020? If yes, provide details on a separate sheet identified as Addendum B.':
            if itemlist[1] == 'Yes':
                itemlist[0] = "Check Box25"
            else:
                itemlist[0] = "Check Box26"
                itemlist[1] = "Yes"
        if itemlist[0] == '5) Is the Applicant (if an individual) or any individual owning 20% or more of the equity of the Applicant subject to an indictment, criminal information, arraignment, or other means by which formal criminal charges are brought in any jurisdiction, or presently incarcerated, or on probation or parole?':
            if itemlist[1] == 'Yes':
                itemlist[0] = "Check Box30"
            else:
                itemlist[0] = "Check Box31"
                itemlist[1] = "Yes"
        if itemlist[0] == '6) Within the last 5 years, for any felony, has the Applicant (if an individual) or any owner of the Applicant 1) been convicted; 2) pleaded guilty; 3) pleaded nolo contendere; 4) been placed on pretrial diversion; or 5) been placed on any form of parole or probation (including probation before judgment)?':
            if itemlist[1] == 'Yes':
                itemlist[0] = "Check Box32"
            else:
                itemlist[0] = "Check Box33"
                itemlist[1] = "Yes"
        if itemlist[0] == '7) Is the United States the principal place of residence for all employees of the Applicant included in the Applicantâ€™s payroll calculation above?':
            if itemlist[1] == 'Yes':
                itemlist[0] = "Check Box34"
            else:
                itemlist[0] = "Check Box35"
                itemlist[1] = "Yes"
        if itemlist[0] == '8) Is the Applicant a franchise that is listed in the SBAâ€™s Franchise Directory?':
            if itemlist[1] == 'Yes':
                itemlist[0] = "Check Box36"
            else:
                itemlist[0] = "Check Box37"
                itemlist[1] = "Yes"

        #Date
        if itemlist[0] == 'Conversion Date':
            itemlist[0] = 'Date'
            itemlist[1] = itemlist[1][0:9]

        item = tuple(itemlist)
        datalist[index] = item

    # Print Name
    datalist.append(("Print Name", full_name))

    # Title
    datalist.append(("Text3", title))

    # Adding Selection choices
    dalist = []
    for i in select_dict:
        datalist.append((i, select_dict[i]))

    form_fill(datalist, row_count)

