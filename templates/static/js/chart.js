// var ctx = document.getElementById('myChart').getContext('2d');
// var myChart;

// function createChart(tasks, progress) {
//   if (myChart) {
//     myChart.destroy(); // Удаляем старый график
//   }
//   myChart = new Chart(ctx, {
//     type: 'bar',
//     data: {
//       labels: tasks,
//       datasets: [
//         {
//           backgroundColor: colors,
//           data: progress,
//         },
//       ],
//     },
//     options: {
//       legend: { display: false },
//       title: {
//         display: true,
//         text: 'TASK PROGRESS %',
//       },
//     },
//   });
// }

// function updateData() {
//   fetch('/data/')
//     .then((response) => response.json())
//     .then((data) => {
//       createChart(data.tasks, data.progress);
//     });
// }

// document.getElementById('updateButton').addEventListener('click', updateData);

// updateData();

var taskTitle = Array.from(document.querySelectorAll('.taskTitle')).map(
  (el) => el.textContent
);
var taskProgress = Array.from(document.querySelectorAll('.taskProgress')).map(
  (el) => parseFloat(el.textContent)
);

Chart.defaults.backgroundColor = '#fff';
Chart.defaults.borderColor = '#fff';
Chart.defaults.color = '#000';
Chart.defaults.font.size = 12;
Chart.defaults.font.family = "'Inter', sans-serif";

var xValues = taskTitle;
var yValues = taskProgress;
var barColors = '#4aaff7';
Chart.defaults.backgroundColor = '#fff';
Chart.defaults.borderColor = '#fff';
Chart.defaults.color = '#000';
Chart.defaults.font.size = 12;
Chart.defaults.font.family = "'Inter', sans-serif";

new Chart('myChart', {
  type: 'bar',
  data: {
    labels: xValues,
    datasets: [
      {
        backgroundColor: barColors,
        data: yValues,
      },
    ],
  },
  options: {
    maintainAspectRatio: false,
    responsive: true,
    legend: { display: true },

    plugins: {
      legend: {
        labels: {
          font: {
            size: 0,
          },
        },
      },
    },
    indexAxis: 'y',
  },
});
