<template>
    <div>
      <table>
        <thead>
          <tr>
            <th @click="sortTable('coin')">Coin <span v-if="currentSort=='coin'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('last_timestamp_reported')">Last Timestamp Reported <span v-if="currentSort=='last_timestamp_reported'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('last_close')">Last Close <span v-if="currentSort=='last_close'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('p')">P <span v-if="currentSort=='p'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('d')">D <span v-if="currentSort=='d'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('q')">Q <span v-if="currentSort=='q'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('next_day_pct_change')">Next Day % Change <span v-if="currentSort=='next_day_pct_change'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('next_day_price')">Next Day Price <span v-if="currentSort=='next_day_price'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('seven_day_pct_change')">Seven Day % Change <span v-if="currentSort=='seven_day_pct_change'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('seven_day_price')">Seven Day Price <span v-if="currentSort=='seven_day_price'">{{ sortAscending ? '▲' : '▼' }}</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in sortedData" :key="item.id">
            <td>{{ item.coin }}</td>
            <td>{{ formatDate(item.last_timestamp_reported) }}</td>
            <td>{{ item.last_close }}</td>
            <td>{{ item.p }}</td>
            <td>{{ item.d }}</td>
            <td>{{ item.q }}</td>
            <td>{{ item.next_day_pct_change }}</td>
            <td>{{ item.next_day_price }}</td>
            <td>{{ item.seven_day_pct_change }}</td>
            <td>{{ item.seven_day_price }}</td>
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
        data: [],
        currentSort: 'coin',
        sortAscending: true
      }
    },
    computed: {
      sortedData() {
        let sortedArray = [...this.data];
        sortedArray.sort((a, b) => {
          let modifier = 1;
          if(!this.sortAscending) modifier = -1;
          
          if(a[this.currentSort] < b[this.currentSort]) return -1 * modifier;
          if(a[this.currentSort] > b[this.currentSort]) return 1 * modifier;
          return 0;
        });
        return sortedArray;
      }
    },
    methods: {
      formatDate(timestamp) {
        const date = new Date(timestamp)
        const year = date.getFullYear()
        const month = ("0" + (date.getMonth() + 1)).slice(-2)
        const day = ("0" + date.getDate()).slice(-2)
        return `${year}-${month}-${day}`
      },
      sortTable(column) {
        if(this.currentSort === column) {
          this.sortAscending = !this.sortAscending;
        } else {
          this.currentSort = column;
          this.sortAscending = true;
        }
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
    cursor: pointer;
  }
  
  th {
    background-color: #f2f2f2;
  }
  </style>
  