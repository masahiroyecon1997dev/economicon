import axios from "axios";

let instance = axios.create({
  baseURL: "http://localhost:8000/api",
});

export default instance;
