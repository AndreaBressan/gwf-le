# TheRaiseOfSlopes (fase iniziale)

Questo plugin QGIS (versione prototipale) permette di:

1. Selezionare un layer DEM caricato nel progetto.
2. Selezionare due punti sulla mappa.
3. Calcolare e visualizzare il profilo altimetrico (distanza vs quota) tra i due punti (campionamento con nearest + fallback bilineare). 
4. Esportare il profilo in CSV (colonne: distanza, quota).

## Installazione sviluppo
Copia la cartella `TheRaiseOfSlopes` nella directory dei plugin utente QGIS:

- macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

Riavvia QGIS e abilita il plugin da Gestore Plugin (essendo "Sperimentale" assicurati di spuntare mostra plugin sperimentali nelle impostazioni del gestore plugin).

## Uso
1. Carica un DEM nel progetto.
2. Avvia il plugin da Menù: TheRaiseOfSlopes -> The Raise Of Slopes - Profilo.
3. Scegli il DEM dal combo.
4. Premi "Seleziona 2 punti" e clicca due volte sulla mappa.
5. Premi "Calcola profilo" per visualizzare il grafico.
6. Esporta se necessario in CSV.

## Dettagli campionamento
Il valore della quota per ogni punto campionato lungo la linea viene ottenuto così:
1. Tentativo di campione puntuale (nearest) tramite provider.sample.
2. Se il valore è nodata o non valido viene usata una interpolazione bilineare sui 4 pixel circostanti.
3. Se uno dei 4 pixel è nodata il risultato viene marcato come None (non tracciato nel grafico).

Passo di campionamento: media della dimensione pixel X/Y del raster (fallback 100 segmenti se dimensioni non disponibili).

## Note
- Fase iniziale: logica di stabilità non ancora implementata.
- Step futuri: metodi dei conci, parametri geotecnici, calcolo fattore di sicurezza, esport dei punti profilo come layer vettoriale, personalizzazione passo.
