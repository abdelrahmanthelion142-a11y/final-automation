# Clinic Appointment Survey Follow-Up Automation

This project is a classic it automation project for a clinic

## Motivation Behind It
well before this project was built a relative of mine had to log in to the crm and manually look at each appoinment the doctor the pateint name the phone number manually type the message and send it to the patient AND EACH WEEK THERE IS LIKE 150 APPOINTMENTS so it was realy time wasting

so i thought there must be a better way to do this so what did i do i created a notebook where i go on the crm and extract the appoinment data by the genius method of (CTRL + C , CTRL + v ) and do that for each page and then the phone numbers of each patinet are not text they are pop image when you hover over the appoinmetnt row so i wrote some javascript to trigger the hover state on each appoinment row take a screen shot of it go to the next and use pytesseract to extract the phone numbers then it normalizes phone numbers uses open ai to determine the names are male or female hen creates a excel file

## The Relization
Umm well insted of all of that why not just call the api i dont know how i didnt think of that all i had to do was just open the devlopoer console view the query and call it using httpx that is it


## Security Note
i can not provide a way to test this automation because that would leak the clinics patient details and appoinmetns so i provided a demo vedio of the github action and the excel file being created

## Tech Stack
well it uses github actions and runs weekly on it i use httpx for calling the api pandas for turning the raw api data into a dataframe to simplify other functions accessing the data i use pydantic to create structured ouput for the llm to classify weather a arabic name is male or female using the open ai package i also use openxl to genrate the excel file (note i know your thinking why not just automaticly send the message using the whatsapp buissines api but it costs money and any third partey tools risk getting the account banned so this is good enough)
also using googles api package to work with google drive and update the classified genders csv and updating the file containing the survey follow up links


## an overview of how it works

1. Fetches the appoinmetns that happend in the last seven days via the api
2. Addes the egypt country code +20 to phone numbers after normalizing them (note that non egyption phone numbers are rare and it would take a lot of effort to implement it so the user sees a phone number with ? in front of it knows its not a valid egyption phone number and can just contact the number on whatsapp cause they recognoise that its maybe saudi number or any number )
3. Classifies patient genders using open ai api and saves their first name to the csv so if they come again in the futureor somone with the same name comes in the future to not have each time to make a open ai call (i could not find a dataset classify arabic /egyptian names on the internet so i am creating one )
4. Translates doctor names to arabic as the messages are in arabic and if specalist are the ones performaing the appoinment it strips the doctor title
5. Exports a Excel file with a clickble link that takes them to the whatsapp acount with the message written
7. Uploads the Excel file to Google Drive (note that the file each time the automation run gets replaced because i dont have google cloud credits so the only thing i can do is replace the file for free)


## Github secretes

1. `EHR_TOKEN` - Bearer token for the API
2. `OPENAI_API_KEY` - OpenAI API key for gender classification
3. `GOOGLE_SERVICE_ACCOUNT_JSON` - JSON credentials for Google Service Account
4. `DRIVE_CSV_FILE_ID` - Google Drive file ID for the gender classification CSV
5. `DRIVE_OUTPUT_FOLDER_ID` - Google Drive folder ID for Excel output uploads

## Project Structure

src/
├── appointments.py      #Api data fetching
├── phone_normalizer.py # Egyptian phone number normalisation
├── gender_classifier.py# Gender classification
├── doctor_translator.py# English→Arabic doctor name translation
├── message_generator.py# Gender-aware Arabic message generation
├── excel_exporter.py   # Excel file with WhatsApp hyperlinks
└── drive_handler.py   # Google Drive upload/download

main.py                # Pipeline orchestrator
requirements.txt       # Python dependencies


## Scheduled Runs

The pipeline runs automatically every Sunday at midnight Egypt time (22:00 UTC Saturday) via GitHub Actions. You can also trigger it manually from the Actions tab in GitHub.