import axios from "../configs/axios";

export async function importCsv(file: File) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = axios.post('/import_csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    console.log(response);
  } catch (error) {
    console.log(error);
  }
}


export async function loadData(tableName: string) {


}
