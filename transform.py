import json
import uuid
import pandas as pd
from confluent_kafka import Consumer, KafkaError

# ---Genom att lägga den i en funktion kan testfil (test_transform.py) "låna" bara den logiken utan att behöva starta hela Kafka-anslutningen.--- Ändring 18-03
def transform_votes(df): 
    vote_mapping = {
        'Ja': 'yes',
        'Nej': 'no',
        'Avstår': 'abstain',
        'Frånvarande': 'absent'
    }
    # Vi kollar om kolumnen 'rost' finns innan vi mappar, för att undvika krasch ---- ÄNDRING 18-03
    if 'rost' in df.columns:
        df['vote_status'] = df['rost'].map(vote_mapping)
    return df

if __name__ == "__main__":
    # All din tunga kod (consumer, while-loop, printar, etc.) ska nu ligga 
    # indragen (tabbad) under denna if-sats.  ----- Ändring 18-03



    consumer_config = {
        'bootstrap.servers': 'kafka:29092',
        'group.id': f'riksdagen_processor_{uuid.uuid4()}',   
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(consumer_config)
    consumer.subscribe(['riksdagen_raw_data'])

    data_buffer = []
    empty_polls = 0
    max_empty_polls = 5

    print("Initiating data extraction from Kafka cluster...", flush=True)

    while True:
        msg = consumer.poll(1.0)
        
        if msg is None:
            empty_polls += 1
            if empty_polls >= max_empty_polls:
                print("Extraction complete. Terminating connection.", flush=True)
                break
            continue
            
        empty_polls = 0
        
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"Consumer error: {msg.error()}", flush=True)
                break
                
        try:
            record = json.loads(msg.value().decode('utf-8'))
            data_buffer.append(record)
        except json.JSONDecodeError:
            pass

    consumer.close()

    df = pd.DataFrame(data_buffer)
    print(f"DataFrame constructed with {len(df)} rows.", flush=True)

    if not df.empty:
        # Calculate the initial data volume
        initial_volume = len(df)
        print(f"Initial row count before duplicate removal: {initial_volume}", flush=True)

        # Execute removal of redundant data based on unique member ID
        df.drop_duplicates(subset=['intressent_id'], keep='first', inplace=True)

        # calculate and print the remaining valid data volume
        final_volume = len(df)
        eliminated_count = initial_volume - final_volume

        print(f"Eradication complete. {eliminated_count} duplicate records destroyed.", flush=True)
        print(f"Current valid data volume: {final_volume} rows.", flush=True)
        
        # --- Step 1: Column Selection ---
        print("\nExecuting column selection...", flush=True)
        columns_to_keep = [
            'intressent_id', 'fodd_ar', 'kon', 'efternamn', 
            'tilltalsnamn', 'parti', 'valkrets', 'status', 'rost', # Ändrin 18-03 lägger till 'rost' eftersom det behövs för vote normalization
        ]
        df = df[columns_to_keep]
        print(f"Columns reduced. Current shape: {df.shape}", flush=True)

        # --- Step 2 & 3: Text Sanitization and Type Conversion ---
        print("\nInitiating strict data sanitization...", flush=True)
        
        # Strip hidden leading/trailing whitespaces safely
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].astype(str).str.strip()

        # Convert empty strings to actual NaN (Null) values
        df.replace('', pd.NA, inplace=True)

        # Enforce strict numerical type for the birth year 
        df['fodd_ar'] = pd.to_numeric(df['fodd_ar'], errors='coerce').astype('Int64')

        # --- Step 5: Normalize Votes (User Story) --- àndring 18-03
        print("\nNormalizing votes to yes/no/abstain...", flush=True)
        vote_mapping = {
            'Ja': 'yes',
            'Nej': 'no',
            'Avstår': 'abstain',
            'Frånvarande': 'absent'
        }
        # Vi skapar den nya kolumnen 'vote_status' som din story kräver
        df['vote_status'] = df['rost'].map(vote_mapping)





        # --- Step 4: Reject Corrupted Data ---
        print("\nExecuting fatal null rejection...", flush=True)
        
        initial_clean_count = len(df)
        # Drop rows completely missing critical primary keys to prevent database failure
        df.dropna(subset=['intressent_id', 'parti'], inplace=True)
        final_clean_count = len(df)

        print(f"Rejection made. {initial_clean_count - final_clean_count} korrupted records  deleted.", flush=True)
        print(f"Final MVP-ready Data Volume: {final_clean_count} rows.", flush=True)

        print("\nFinal DataFrame Structure:", flush=True)
        print(df.info(), flush=True)

    else:
        print("The df is empty. No data was extracted.", flush=True)

    # -- Note--: The verification steps below are for me and you guys (Christoffer, Hannah ) too see if the transformation was successful. ---


    # --- Objective Verification Step ---
    print("\n--- RAW DATA CHECK ---")
    # Visa de 5 första raderna för att se att kolumnerna faktiskt är borta
    print("First 5 rows (Selected columns only):")
    print(df.head())

    print("\n--- DATA TYPE CHECK ---")
    # Visa exakta datatyper för att bevisa att fodd_ar inte är text
    print(df.dtypes)

    print("\n--- NULL VALUE PROOF ---")
    # Visa exakt hur många tomma värden som finns kvar
    print(df.isnull().sum())

    # testar om det funkar   Ändring 18-03

    print("\n--- VOTE NORMALIZATION CHECK ---")
    print(df[['rost', 'vote_status']].head(10))  