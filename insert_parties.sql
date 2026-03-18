-- insert_parties.sql
-- Run once after create_tables.sql
-- color_hex values are official party brand colors

INSERT INTO parties (party_id, party_name, color_hex) VALUES
    ('S',  'Socialdemokraterna',       '#E8112d'),
    ('SD', 'Sverigedemokraterna',      '#DDDD00'),
    ('M',  'Moderaterna',              '#52BDEC'),
    ('C',  'Centerpartiet',            '#009933'),
    ('V',  'Vänsterpartiet',           '#DA291C'),
    ('KD', 'Kristdemokraterna',        '#000077'),
    ('MP', 'Miljöpartiet',             '#83CF39'),
    ('L',  'Liberalerna',              '#006AB3'),
    ('-',  'Parti okänt/saknas',       NULL)
ON CONFLICT (party_id) DO NOTHING;