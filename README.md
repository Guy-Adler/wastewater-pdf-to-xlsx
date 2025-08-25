## Running

Install all dependencies:

```shell
$ pip install -r requirements.txt
```

Run the application:

```shell
$ python3 app.py
```

## Configuration options (schemas)

### Extract

Extract schemas are stored in [schemas/extract/](schemas/extract/)

```ts
{
  name: string; // name of the lab performing the tests
  identifierRegex: string; // Regex used to test if document matches schema
  samplingDateExtractionRegex: string; // Regex used to extract the sampling date. Needs to have a capture group named `date` (e.g. `(?P<date>[0-9]{2}/[0-9]{2}/[0-9]{2})`)
  type: {
    [key: string]: string; // Key is a regex used to test if document matches type, value is the type name (used in later schemas). Having a document which can match multiple keys is considered undefined behavior.
  }
  tables: {
    results: {
      tableNumber: number; // The 0 based index of the table in the list of tables in the document
      headerRowCount?: number; // Amount of rows to consider as headers and skip when loading data. 0 if omitted.
      columns: {
        [key: number]: Array<string>; // Key is the number of columns in the table. The value is an array, matching each column to a column title (first value in the array is the first column, LTR). The values `result` and `testName` are required.
      }
    }
  }
}
```

### Transform

Transform schemas are stored in [schemas/transform/](schemas/transform/)

```ts
{
  dateFormat: string; // Python date format of the extracted sampling date
  tables: {
    results: {
      testNames: {
        [key: string]: string; // Mapping between the values of the extracted column marked `testName` and a standardized name used in the load schema.
      }
    }
  }
}

```

### Load

Load schemas are stored in [schemas/load/](schemas/load/)

```ts
{
  name: string; // Name of the treatment plant
  sheets: {
    [key: string]: { // key is a test type
      name: string; // Name of the Excel sheet
      headerRowCount?: number; // Number of header rows in the Excel sheet. 0 if not specified
      addMissingRows?: boolean; // Whether rows for missing dates should be added. Default true.
      fields: {
        [key: string]: { // key is a standardized test name
          column: string; // The column in the Excel sheet the results maps to
        }
      }
    }
  }
}
```
