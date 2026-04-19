document.addEventListener('DOMContentLoaded', () => {
    // Mobile Navbar Toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            mobileToggle.classList.toggle('active');
            navLinks.classList.toggle('active');
        });
    }

    // Scroll Header Style
    const nav = document.querySelector('nav');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    });

    // Reveal Animations on Scroll
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

    // Active Link Highlighting
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage) {
            link.classList.add('active');
        }
    });

    // Smooth Scroll for Internal Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                if (navLinks.classList.contains('active')) {
                    mobileToggle.classList.remove('active');
                    navLinks.classList.remove('active');
                }
            }
        });
    });
    // --- Dashboard & Modal Logic ---

    // Modal state
    window.openModal = (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            setTimeout(() => modal.classList.add('active'), 10);
            document.body.style.overflow = 'hidden';
        }
    };

    window.closeModal = (modalId) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            setTimeout(() => {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }, 300);
        }
    };

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            closeModal(e.target.id);
        }
    });

    // Post New Task
    const postTaskBtn = document.getElementById('postTaskBtn');
    const postTaskForm = document.getElementById('postTaskForm');
    const activeTasksContainer = document.getElementById('activeTasksContainer');

    if (postTaskBtn) {
        postTaskBtn.addEventListener('click', () => openModal('postTaskModal'));
    }

    if (postTaskForm) {
        postTaskForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const title = document.getElementById('taskTitle').value;
            const desc = document.getElementById('taskDesc').value;
            const budget = document.getElementById('taskBudget').value;
            const deadline = document.getElementById('taskDeadline').value;
            const category = document.getElementById('taskCategory').value;

            // Create new task card
            const taskCard = document.createElement('div');
            taskCard.className = 'glass-card task-info-card reveal active';
            taskCard.innerHTML = `
                <div>
                    <h3 style="font-size: 1.5rem; margin-bottom: 0.5rem;">${title}</h3>
                    <p style="color: var(--text-muted);">Budget: ₹${budget} • Deadline: ${deadline} • ${category}</p>
                </div>
                <div style="text-align: right;">
                    <span class="badge" style="font-size: 1rem; padding: 0.5rem 1.5rem;">0 Applicants Waiting</span>
                </div>
            `;

            // Add to container
            if (activeTasksContainer) {
                activeTasksContainer.prepend(taskCard);
            }

            // Success feedback
            if (typeof showToast === 'function') {
                showToast('Task posted successfully!');
            }

            // reset and close
            postTaskForm.reset();
            closeModal('postTaskModal');
        });
    }

    // Hire Student
    let pendingHireButton = null;
    let pendingStudentName = '';

    const hireBtns = document.querySelectorAll('.hire-student-btn');
    const hireModal = document.getElementById('hireModal');
    const hireModalText = document.getElementById('hireModalText');
    const confirmHireBtn = document.getElementById('confirmHireBtn');

    if (hireBtns.length > 0) {
        hireBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                pendingHireButton = btn;
                pendingStudentName = btn.getAttribute('data-student-name');
                if (hireModalText) {
                    hireModalText.innerText = `Are you sure you want to hire ${pendingStudentName} for this task?`;
                }
                openModal('hireModal');
            });
        });
    }

    if (confirmHireBtn) {
        confirmHireBtn.addEventListener('click', () => {
            if (pendingHireButton) {
                pendingHireButton.innerText = 'Hired ✓';
                pendingHireButton.classList.remove('btn-primary');
                pendingHireButton.classList.add('btn-hired');
                pendingHireButton.disabled = true;

                if (typeof showToast === 'function') {
                    showToast(`${pendingStudentName} has been hired successfully.`);
                }
                closeModal('hireModal');
            }
        });
    }

    // Toast Utility
    window.showToast = (message) => {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = `
            <svg style="width: 20px; height: 20px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };
});
