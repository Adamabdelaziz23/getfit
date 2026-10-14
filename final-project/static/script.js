const menuBtn = document.querySelector('.menu-btn');
const dropdownMenu = document.getElementById('dropdownmenu');

document.addEventListener("DOMContentLoaded", function() {
    const menuBtn = document.querySelector(".menu-btn");
    const dropdownMenu = document.getElementById("dropdownmenu");

    if (menuBtn && dropdownMenu) {
        // Hide menu by default on load
        dropdownMenu.style.display = "none";

        // Toggle menu display on click
        menuBtn.addEventListener("click", function(event) {
            event.stopPropagation();
            if (dropdownMenu.style.display === "none" || dropdownMenu.style.display === "") {
                dropdownMenu.style.display = "block";
            } else {
                dropdownMenu.style.display = "none";
            }
        });

        // Close menu when clicking anywhere else on the page
        document.addEventListener("click", function(event) {
            if (!dropdownMenu.contains(event.target) && !menuBtn.contains(event.target)) {
                dropdownMenu.style.display = "none";
            }
        });
    }
});


// Calorie Calculator Logic
const calcForm = document.getElementById('calcForm');
if (calcForm) {
    calcForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const age = parseInt(document.getElementById('age').value);
        const gender = document.getElementById('gender').value;
        const weight = parseFloat(document.getElementById('weight').value);
        const height = parseFloat(document.getElementById('height').value);
        // BMR Calculation
        let bmr = (10 * weight) + (6.25 * height) - (5 * age);
        bmr += (gender === 'male') ? 5 : -161;
        // Estimated maintenance calories (light activity factor ~1.375)
        const totalCalories = Math.round(bmr * 1.375);
        const resultDiv = document.getElementById('calcResult');
        resultDiv.style.display = 'block';
        resultDiv.innerText =
            `Your Estimated Maintenance Calories: ${totalCalories} kcal/day`;
    });
}
// Rest Timer Logic
let timerInterval = null;

function startTimer(seconds) {
    clearInterval(timerInterval);
    let remainingTime = seconds;
    updateTimerDisplay(remainingTime);
    timerInterval = setInterval(() => {
        remainingTime--;
        updateTimerDisplay(remainingTime);
        if (remainingTime <= 0) {
            clearInterval(timerInterval);
            alert("Rest time is up! Get back to work!");
        }
    }, 1000);
}

function resetTimer() {
    clearInterval(timerInterval);
    const display = document.getElementById("timerDisplay");
    if (display) display.innerText = "01:00";
}

function updateTimerDisplay(seconds) {
    const display = document.getElementById("timerDisplay");
    if (!display) return;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    display.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}
// Update Personal Records (PRs)
const prForm = document.getElementById('prForm');
if (prForm) {
    prForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const exercise = document.getElementById('exerciseSelect').value;
        const weight = document.getElementById('prWeightInput').value;
        if (exercise === 'bench') document.getElementById('benchPr').innerText =
            `${weight} kg`;
        if (exercise === 'squat') document.getElementById('squatPr').innerText =
            `${weight} kg`;
        if (exercise === 'deadlift') document.getElementById('deadliftPr').innerText =
            `${weight} kg`;
        document.getElementById('prWeightInput').value = '';
    });
}

// Edit Profile Details
const editProfileForm = document.getElementById('editProfileForm');
if (editProfileForm) {
    editProfileForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Update user stats on page
        document.getElementById('userName').innerText = document.getElementById('editName')
            .value;
        document.getElementById('userWeight').innerText =
            `${document.getElementById('editWeight').value} kg`;
        document.getElementById('userHeight').innerText =
            `${document.getElementById('editHeight').value} cm`;
        document.getElementById('userGoal').innerText = document.getElementById('editGoal')
            .value;

        // Hide the Bootstrap modal automatically
        const modalElement = document.getElementById('editProfileModal');
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
}
