import pandas as pd
# Här importerar vi funktionen från din transform.py
from transform import transform_votes 

def test_normalize_votes_logic():
    # Vi skapar en låtsas-dataframe (mock data)
    data = {
        'rost': ['Ja', 'Nej', 'Avstår', 'Frånvarande'],
        'intressent_id': ['1', '2', '3', '4'],
        'beteckning': ['FiU20', 'FiU20', 'FiU20', 'FiU20']
    }
    df = pd.DataFrame(data)
    
    # Kör funktion
    transformed_df = transform_votes(df)
    
    # Kolla att värdena blev rätt transformerade
    assert transformed_df.iloc[0]['vote_status'] == 'yes'
    assert transformed_df.iloc[1]['vote_status'] == 'no'
    assert transformed_df.iloc[2]['vote_status'] == 'abstain'
    assert transformed_df.iloc[3]['vote_status'] == 'absent'