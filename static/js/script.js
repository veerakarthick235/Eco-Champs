document.addEventListener('DOMContentLoaded', () => {
    // --- Quiz Elements ---
    const startQuizBtn = document.getElementById('start-quiz-btn');
    const quizSetupContainer = document.getElementById('quiz-setup');
    const quizMainContainer = document.getElementById('quiz-main-container');
    const quizNavigation = document.getElementById('quiz-navigation');
    const quizResultContainer = document.getElementById('quiz-result');
    const questionDisplay = document.getElementById('question-display-area');
    const questionPalette = document.getElementById('question-palette');
    const quizTopicSelect = document.getElementById('quiz-topic');

    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const markReviewBtn = document.getElementById('mark-review-btn');
    const submitQuizBtn = document.getElementById('submit-quiz-btn');

    // --- Quiz State Variables ---
    let allQuestions = [];
    let userAnswers = [];
    let reviewStatus = [];
    let currentQuestionIndex = 0;

    if (startQuizBtn) {
        startQuizBtn.addEventListener('click', startQuiz);
    }

    async function startQuiz() {
        const topic = quizTopicSelect.value;
        startQuizBtn.textContent = 'Generating...';
        startQuizBtn.disabled = true;

        try {
            const response = await fetch('/generate_quiz', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: topic })
            });
            if (!response.ok) throw new Error('Failed to generate quiz.');

            const data = await response.json();
            allQuestions = data.questions;
            
            // Check if we received valid questions
            if (!allQuestions || allQuestions.length === 0) {
                throw new Error('No questions were loaded for this topic.');
            }

            initializeQuizState();
            renderPalette();
            displayQuestion(0);

            quizSetupContainer.classList.add('hidden');
            quizMainContainer.classList.remove('hidden');
            quizNavigation.classList.remove('hidden');

        } catch (error) {
            // Display error in a more user-friendly way
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger';
            errorDiv.textContent = `Error: ${error.message}`;
            quizSetupContainer.parentNode.insertBefore(errorDiv, quizSetupContainer.nextSibling);

        } finally {
            startQuizBtn.textContent = 'Start Quiz';
            startQuizBtn.disabled = false;
        }
    }

    function initializeQuizState() {
        userAnswers = new Array(allQuestions.length).fill(null);
        reviewStatus = new Array(allQuestions.length).fill(false);
        currentQuestionIndex = 0;
    }

    function renderPalette() {
        questionPalette.innerHTML = '';
        allQuestions.forEach((_, index) => {
            const paletteBtn = document.createElement('button');
            paletteBtn.className = 'palette-btn not-answered';
            paletteBtn.id = `palette-btn-${index}`;
            paletteBtn.textContent = index + 1;
            paletteBtn.addEventListener('click', () => displayQuestion(index));
            questionPalette.appendChild(paletteBtn);
        });
    }

    function displayQuestion(index) {
        currentQuestionIndex = index;
        const q = allQuestions[index];

        let optionsHTML = '';
        q.options.forEach((option, i) => {
            const isChecked = userAnswers[index] === option ? 'checked' : '';
            optionsHTML += `
                <li>
                    <label>
                        <input type="radio" name="question-${index}" value="${option}" ${isChecked}>
                        ${option}
                    </label>
                </li>
            `;
        });

        questionDisplay.innerHTML = `
            <div class="question-card">
                <h3>Question ${index + 1}: ${q.question_text}</h3>
                <ul class="options-list">${optionsHTML}</ul>
            </div>
        `;

        // Add event listeners to the new radio buttons
        document.querySelectorAll(`input[name="question-${index}"]`).forEach(input => {
            input.addEventListener('change', (e) => {
                userAnswers[index] = e.target.value;
                updatePaletteStatus(index);
            });
        });

        updateNavigationButtons();
        updatePaletteHighlight();
    }
    
    function updatePaletteStatus(index) {
        const paletteBtn = document.getElementById(`palette-btn-${index}`);
        paletteBtn.classList.remove('not-answered', 'answered', 'marked-for-review');

        if (reviewStatus[index]) {
            paletteBtn.classList.add('marked-for-review');
        } else if (userAnswers[index] !== null) {
            paletteBtn.classList.add('answered');
        } else {
            paletteBtn.classList.add('not-answered');
        }
    }

    function updatePaletteHighlight() {
        document.querySelectorAll('.palette-btn').forEach(btn => {
            btn.classList.remove('current');
        });
        document.getElementById(`palette-btn-${currentQuestionIndex}`).classList.add('current');
    }
    
    function updateNavigationButtons() {
        prevBtn.disabled = currentQuestionIndex === 0;
        nextBtn.disabled = currentQuestionIndex === allQuestions.length - 1;
        markReviewBtn.textContent = reviewStatus[currentQuestionIndex] ? 'Unmark Review' : 'Mark for Review';
    }

    // --- Navigation Event Listeners ---
    nextBtn.addEventListener('click', () => {
        if (currentQuestionIndex < allQuestions.length - 1) {
            displayQuestion(currentQuestionIndex + 1);
        }
    });

    prevBtn.addEventListener('click', () => {
        if (currentQuestionIndex > 0) {
            displayQuestion(currentQuestionIndex - 1);
        }
    });

    markReviewBtn.addEventListener('click', () => {
        reviewStatus[currentQuestionIndex] = !reviewStatus[currentQuestionIndex];
        updatePaletteStatus(currentQuestionIndex);
        updateNavigationButtons();
    });

    submitQuizBtn.addEventListener('click', () => {
        const unansweredCount = userAnswers.filter(ans => ans === null).length;
        let confirmationMessage = "Are you sure you want to submit?";
        if (unansweredCount > 0) {
            confirmationMessage += `\nYou have ${unansweredCount} unanswered questions.`;
        }

        if (confirm(confirmationMessage)) {
            handleQuizSubmit();
        }
    });

    async function handleQuizSubmit() {
        try {
            const response = await fetch('/submit_quiz', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers: userAnswers })
            });
            if (!response.ok) throw new Error('Failed to submit quiz.');

            const result = await response.json();
            displayResult(result);

        } catch (error) {
            quizResultContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
            quizResultContainer.classList.remove('hidden');
        }
    }

    function displayResult(result) {
        quizMainContainer.classList.add('hidden');
        quizNavigation.classList.add('hidden');
        quizResultContainer.innerHTML = `
            <div class="card">
                <h2>Quiz Complete!</h2>
                <p>You scored <strong>${result.score} out of ${result.total}</strong>.</p>
                <p>You have earned <strong>${result.points_earned} Eco-Points!</strong></p>
                <a href="/dashboard" class="btn">Back to Dashboard</a>
            </div>
        `;
        quizResultContainer.classList.remove('hidden');
    }
});