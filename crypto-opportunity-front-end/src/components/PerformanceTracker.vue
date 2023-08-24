<template>
    <div>
      <table>
        <thead>
          <tr>
            <th @click="sortTable('coin')">Coin <span v-if="currentSort=='coin'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('last_timestamp_reported')">Last Timestamp Reported <span v-if="currentSort=='last_timestamp_reported'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('p')">P <span v-if="currentSort=='p'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('d')">D <span v-if="currentSort=='d'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('q')">Q <span v-if="currentSort=='q'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('total_performance')">Total Perf <span v-if="currentSort=='total_performance'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('total_performance_vs_coin')">Total Perf vs Coin <span v-if="currentSort=='total_performance_vs_coin'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('last_month_performance')">Last Month<span v-if="currentSort=='last_month_performance'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('last_week_performance')">Last Week<span v-if="currentSort=='last_week_performance'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('last_day_performance')">Last Day<span v-if="currentSort=='last_day_performance'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('hold_performance')">Hold Performance <span v-if="currentSort=='hold_performance'">{{ sortAscending ? '▲' : '▼' }}</span></th>
            <th @click="sortTable('total_days')">Days Since Start <span v-if="currentSort=='total_days'">{{ sortAscending ? '▲' : '▼' }}</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in sortedData" :key="item.id">
            <td>{{ item.coin }}</td>
            <td>{{ formatDate(item.last_timestamp_reported) }}</td>
            <td>{{ item.p }}</td>
            <td>{{ item.d }}</td>
            <td>{{ item.q }}</td>
            <td>{{ item.total_performance }}</td>
            <td>{{ item.total_performance_vs_coin }}</td>
            <td>{{ item.last_month_performance }}</td>
            <td>{{ item.last_week_performance }}</td>
            <td>{{ item.last_day_performance }}</td>
            <td>{{ item.hold_performance }}</td>
            <td>{{ item.total_days }}</td>
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
      const response = await axios.get('http://45.56.125.213:5002/all-model-performance')
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
  