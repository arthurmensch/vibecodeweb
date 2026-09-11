/* global DEMOGRAPHICS, Chart */
(function () {
  'use strict';

  var D = window.DEMOGRAPHICS;
  var GENDER_LABELS = { M: 'Male', F: 'Female', X: 'Undisclosed' };
  var GENDER_COLORS = { M: '#3b82f6', F: '#ec4899', X: '#94a3b8' };
  var GROUP_COLORS = ['#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#94a3b8'];
  var selectedGroup = null;

  var allBucketKeys = Object.keys(D.ageBuckets).map(Number).sort(function (a, b) { return a - b; });

  function bucketLabel(lo) {
    return lo + '-' + (lo + 4);
  }

  function pct(n, total) {
    return total ? (100 * n / total).toFixed(1) + '%' : '-';
  }

  function genderCount(source, key) {
    return (source && source.gender && source.gender[key]) || 0;
  }

  function filteredData() {
    if (!selectedGroup) {
      return {
        buckets: D.ageBuckets,
        gender: Object.keys(GENDER_LABELS).reduce(function (acc, k) {
          var sum = 0;
          D.groupOrder.forEach(function (g) { sum += genderCount(D.groups[g], k); });
          acc[k] = sum;
          return acc;
        }, {})
      };
    }
    return {
      buckets: (D.groupsAgeBuckets && D.groupsAgeBuckets[selectedGroup]) || {},
      gender: (D.groups[selectedGroup] && D.groups[selectedGroup].gender) || {}
    };
  }

  function bucketGender(b, key) {
    if (!b) return 0;
    if (b.gender) return b.gender[key] || 0;
    return b[key] || 0;
  }

  function bucketSum(b) {
    var sum = 0;
    Object.keys(GENDER_LABELS).forEach(function (k) { sum += bucketGender(b, k); });
    return sum;
  }

  function bucketTotals(buckets) {
    return allBucketKeys.map(function (lo) {
      return bucketSum(buckets[String(lo)]);
    });
  }

  function weightedMean(buckets) {
    var sum = 0, count = 0;
    allBucketKeys.forEach(function (lo) {
      var n = bucketSum(buckets[String(lo)]);
      sum += (lo + 2) * n;
      count += n;
    });
    return count ? sum / count : 0;
  }

  function bucketMedian(buckets) {
    var values = [];
    allBucketKeys.forEach(function (lo) {
      var n = bucketSum(buckets[String(lo)]);
      for (var i = 0; i < n; i++) values.push(lo + 2);
    });
    if (!values.length) return 0;
    values.sort(function (a, b) { return a - b; });
    var mid = Math.floor(values.length / 2);
    return values.length % 2 ? values[mid] : (values[mid - 1] + values[mid]) / 2;
  }

  var charts = {};

  function initKpis(data) {
    var total = Object.keys(GENDER_LABELS).reduce(function (acc, k) { return acc + data.gender[k]; }, 0);
    document.querySelector('#kpi-total .kpi-value').textContent = total;
    document.querySelector('#kpi-male .kpi-value').textContent = pct(data.gender.M, total);
    document.querySelector('#kpi-female .kpi-value').textContent = pct(data.gender.F, total);
    document.querySelector('#kpi-undisclosed .kpi-value').textContent = pct(data.gender.X, total);
    document.querySelector('#kpi-mean .kpi-value').textContent = weightedMean(data.buckets).toFixed(1);
    document.querySelector('#kpi-median .kpi-value').textContent = bucketMedian(data.buckets).toFixed(1);
  }

  function renderAgeChart(data) {
    var ctx = document.getElementById('chart-age').getContext('2d');
    var config = {
      type: 'bar',
      data: {
        labels: allBucketKeys.map(bucketLabel),
        datasets: [{
          label: 'Headcount',
          data: bucketTotals(data.buckets),
          backgroundColor: selectedGroup ? GROUP_COLORS[D.groupOrder.indexOf(selectedGroup)] : '#3b82f6'
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { title: { display: true, text: 'Age band' } },
          y: { title: { display: true, text: 'People' }, beginAtZero: true }
        }
      }
    };
    if (charts.age) {
      charts.age.data = config.data;
      charts.age.update();
    } else {
      charts.age = new Chart(ctx, config);
    }
  }

  function renderGenderChart(data) {
    var ctx = document.getElementById('chart-gender').getContext('2d');
    var config = {
      type: 'doughnut',
      data: {
        labels: Object.keys(GENDER_LABELS).map(function (k) { return GENDER_LABELS[k]; }),
        datasets: [{
          data: Object.keys(GENDER_LABELS).map(function (k) { return data.gender[k]; }),
          backgroundColor: Object.keys(GENDER_LABELS).map(function (k) { return GENDER_COLORS[k]; })
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: function (item) {
                var total = item.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                return ' ' + item.label + ': ' + item.raw + ' (' + pct(item.raw, total) + ')';
              }
            }
          }
        }
      }
    };
    if (charts.gender) {
      charts.gender.data = config.data;
      charts.gender.update();
    } else {
      charts.gender = new Chart(ctx, config);
    }
  }

  function renderGroupChart() {
    var ctx = document.getElementById('chart-gender-dept').getContext('2d');
    var config = {
      type: 'bar',
      data: {
        labels: D.groupOrder,
        datasets: Object.keys(GENDER_LABELS).map(function (k) {
          return {
            label: GENDER_LABELS[k],
            data: D.groupOrder.map(function (g) { return genderCount(D.groups[g], k); }),
            backgroundColor: GENDER_COLORS[k]
          };
        })
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom' } },
        scales: {
          x: { stacked: true, title: { display: true, text: 'Department group' } },
          y: { stacked: true, title: { display: true, text: 'People' }, beginAtZero: true }
        }
      }
    };
    if (charts.groups) {
      charts.groups.data = config.data;
      charts.groups.update();
    } else {
      charts.groups = new Chart(ctx, config);
    }
  }

  function renderGroupCards() {
    var container = document.getElementById('group-cards');
    container.innerHTML = '';
    D.groupOrder.forEach(function (g, i) {
      var info = D.groups[g];
      var total = info ? info.count : 0;
      var female = genderCount(info, 'F');
      var male = genderCount(info, 'M');
      var card = document.createElement('button');
      card.type = 'button';
      card.className = 'group-card' + (selectedGroup === g ? ' selected' : '');
      card.innerHTML =
        '<h3>' + g + '</h3>' +
        '<p class="group-count">' + total + ' people</p>' +
        '<p class="group-gender">' +
          '<span style="color:' + GENDER_COLORS.M + '">' + male + '</span> / ' +
          '<span style="color:' + GENDER_COLORS.F + '">' + female + '</span>' +
        '</p>' +
        '<p class="group-share">' + pct(female, total) + ' female</p>' +
        '<span class="swatch" style="background:' + GROUP_COLORS[i] + '"></span>';
      card.addEventListener('click', function () {
        selectedGroup = selectedGroup === g ? null : g;
        update();
      });
      container.appendChild(card);
    });
  }

  function update() {
    var data = filteredData();
    initKpis(data);
    renderAgeChart(data);
    renderGenderChart(data);
    renderGroupCards();
    document.getElementById('subtitle').textContent = selectedGroup
      ? 'Filtered: ' + selectedGroup
      : 'Age distribution and gender split across the company';
  }

  function init() {
    document.getElementById('subtitle').textContent =
      'Age distribution and gender split across the company';
    document.getElementById('asof').textContent = D.asOf;
    document.getElementById('source-link').href =
      'https://docs.google.com/spreadsheets/d/1Cdl9IOKeC9ZtIxeEsFkMML6xysrtgu5umdnst41v3xs/edit?gid=0#gid=0';
    renderGroupChart();
    update();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
