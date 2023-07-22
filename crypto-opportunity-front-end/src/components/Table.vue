<template>
    <div>
      <table>
        <thead>
          <tr>
            <th>Coin</th>
            <th>Last Timestamp Reported</th>
            <th>Last Close</th>
            <th>Next Day Price</th>
            <th>Next Day % Change</th>
            <th>Seven Day Price</th>
            <th>Seven Day % Change</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in data" :key="item.coin">
            <td>{{ item.coin }}</td>
            <td>{{ item.last_timestamp_reported }}</td>
            <td>{{ item.last_close }}</td>
            <td>{{ item.next_day_price }}</td>
            <td>{{ item.next_day_pct_change }}</td>
            <td>{{ item.seven_day_price }}</td>
            <td>{{ item.seven_day_pct_change }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    data() {
      return {
        data: []
      }
    },
    async created() {
      const response = await axios.get('http://45.56.125.213:5002/forecast-results-all')
      this.data = response.data
    }
  }
  </script>
  
  <style scoped>
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  th, td {
    border: 1px solid black;
    padding: 8px;
    text-align: left;
  }
  
  th {
    background-color: #f2f2f2;
  }
  </style>
  