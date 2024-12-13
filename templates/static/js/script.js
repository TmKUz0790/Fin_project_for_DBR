var barProgress = document.querySelector('.progress-bar');
var newBarProgress = parseFloat(barProgress.textContent);
newBarProgress = newBarProgress;

barProgress.textContent = newBarProgress + '%';
barProgress.style.width = newBarProgress + '%';

if (newBarProgress < 30) {
  barProgress.style.backgroundColor = '#e60000';
  barProgress.style.animationName = 'glowing-red';
} else if (newBarProgress < 65) {
  barProgress.style.backgroundColor = '#ffb700';
  barProgress.style.animationName = 'glowing-yellow';
} else if (newBarProgress < 100) {
  barProgress.style.backgroundColor = '#00ff44';
  barProgress.style.animationName = 'glowing-green';
} else {
  barProgress.style.backgroundColor = '#0073e6';
  barProgress.style.animationName = 'glowing';
}

var modalNew = document.getElementById('myModal');
var btn = document.querySelector('.feed_back_menu');
var span = document.querySelector('.close');

// Открытие модального окна при нажатии на кнопку
btn.onclick = function () {
  modalNew.style.display = 'block';
};

// Закрытие модального окна при нажатии на крестик
span.onclick = function () {
  modalNew.style.display = 'none';
};

// Закрытие модального окна при клике вне окна
window.onclick = function (event) {
  if (event.target == modalNew) {
    modalNew.style.display = 'none';
  }
};
