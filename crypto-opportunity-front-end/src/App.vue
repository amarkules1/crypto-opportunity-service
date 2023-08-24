<template>
  <div id="app">
    <nav class="header">
      <div class="title">Coin Performance Tracker</div>
      <div class="nav-buttons">
        <button class="btn" @click=refreshData()>refresh data</button>
        <router-link class="btn" active-class="active" to="/cointable">Forecasts</router-link>
        <router-link class="btn" active-class="active" to="/performancetracker">Performance Tracker</router-link>
      </div>
    </nav>
    <!-- Where the component will be displayed -->
    <router-view/>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'App',

  methods: {
    refreshData() {
      axios.get('http://45.56.125.213:5002/forecast-results-async')
    }
  }
}
</script>

<style scoped>
.header {
  background-color: black;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-buttons {
  display: flex;
}

.btn {
  text-decoration: none;
  color: white;
  border: 1px solid white;
  padding: 10px;
  margin-right: 10px;
  background-color: black;
  transition: background-color 0.3s;
}

.btn.active {
  background-color: white;
  color: black;
}

.btn:hover {
  background-color: grey;
}

.title {
  color: white;
  font-size: 20px;
}
</style>
