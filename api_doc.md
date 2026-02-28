# Transcribe & Validate Command API

## Endpoint
`POST /v1/api/transcribe/command`

---

## Description
Uploads an audio recording along with a list of beneficiaries.  
The API will:

- Transcribe the audio into text.  
- Attempt to identify transaction-style commands (e.g., “Send 50,000 to Hamza Ahmed in Standard Chartered”).  
- Return the transcription result and any matched information.  

---

## Request

### Content-Type
`multipart/form-data`

### Parameters

- **audio_file** (UploadFile, required)  
  - The recorded audio file. Must be in a supported audio format (e.g., `.webm`, `.wav`, `.mp3`).  
  - Maximum size: 25 MB.  

- **beneficiaries_data** (string, required)  
  - A JSON string of beneficiaries that can be matched against the transcription.  

  **Example**:  
  ```json
  [
    { "id": "uuid1", "name": "Mubashir Ali", "account": "PK00-0001-1111-2222", "bank": "Alfalah" },
    { "id": "uuid2", "name": "Ali Raza", "account": "PK00-0002-1111-2222", "bank": "United Bank" }
  ]


#### Frontend JS Code:
- const formData = new FormData();
- formData.append("audio_file", audioBlob, "recording.webm");
- formData.append("beneficiaries_data", JSON.stringify(beneficiaries));

### CURL Request
- curl -X POST http://localhost:8000/v1/api/transcribe/command \
  -F "audio_file=@recording.webm" \
  -F 'beneficiaries_data=[
    {"id":"uuid1","name":"Mubashir Ali","account":"PK00-0001-1111-2222","bank":"Alfalah"},
    {"id":"uuid2","name":"Ali Raza","account":"PK00-0002-1111-2222","bank":"United Bank"}
  ]'
