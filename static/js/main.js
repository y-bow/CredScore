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

    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        // Load preference
        const savedTheme = localStorage.getItem('theme') || 'dark';
        if (savedTheme === 'light') {
            document.body.classList.replace('theme-dark', 'theme-light');
            themeToggle.innerText = '☀️';
        }

        themeToggle.addEventListener('click', () => {
            if (document.body.classList.contains('theme-dark')) {
                document.body.classList.replace('theme-dark', 'theme-light');
                localStorage.setItem('theme', 'light');
                themeToggle.innerText = '☀️';
            } else {
                document.body.classList.replace('theme-light', 'theme-dark');
                localStorage.setItem('theme', 'dark');
                themeToggle.innerText = '🌙';
            }
        });
    }

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

    // --- Modal Logic ---
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

    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            closeModal(e.target.id);
        }
    });

    // Share Profile
    const shareProfileBtn = document.getElementById('shareProfileBtn');
    if (shareProfileBtn) {
        shareProfileBtn.addEventListener('click', () => {
            const profileId = shareProfileBtn.getAttribute('data-profile-id');
            const url = window.location.origin + '/profile/' + profileId;
            navigator.clipboard.writeText(url).then(() => {
                showToast('Profile link copied!');
            });
        });
    }

    // Category Filtering (Explore Page)
    const filterBtns = document.querySelectorAll('.filter-btn');
    if (filterBtns.length > 0) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const category = btn.innerText.trim();
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                document.querySelectorAll('.task-card').forEach(card => {
                    if (category === 'All' || card.getAttribute('data-category') === category) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }

    // Toast Utility
    window.showToast = (message, isError = false) => {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast';
        if (isError) {
            toast.style.background = 'rgba(239, 68, 68, 0.9)';
            toast.style.borderLeft = '4px solid #991B1B';
        }
        toast.innerHTML = `
            <span>${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    };
});

// AJAX Functions
function applyTask(btn, taskId) {
    fetch('/apply/' + taskId, {
        method: 'POST',
    }).then(res => res.json()).then(data => {
        if (data.success) {
            btn.innerText = 'Applied ✓';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline');
            btn.disabled = true;
            openModal('applyModal');
        } else {
            showToast(data.message || 'Error applying to task', true);
        }
    });
}

let pendingTaskId = null;
let pendingStudentId = null;

function promptHire(btn, taskId, studentId, studentName) {
    pendingTaskId = taskId;
    pendingStudentId = studentId;
    document.getElementById('hireModalText').innerText = `Are you sure you want to hire ${studentName} for this task?`;
    document.getElementById('confirmHireBtn').onclick = () => confirmHire(btn);
    openModal('hireModal');
}

function confirmHire(btn) {
    const formData = new FormData();
    formData.append('task_id', pendingTaskId);
    formData.append('student_id', pendingStudentId);

    fetch('/task/hire', {
        method: 'POST',
        body: formData
    }).then(res => res.json()).then(data => {
        if (data.success) {
            btn.innerText = 'Hired ✓';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-hired');
            btn.disabled = true;
            showToast('Student has been hired successfully.');
            closeModal('hireModal');
            setTimeout(() => location.reload(), 1500); // reload to update lists
        } else {
            showToast('Error hiring student', true);
        }
    });
}

function completeTask(taskId) {
    const formData = new FormData();
    formData.append('task_id', taskId);

    fetch('/task/complete', {
        method: 'POST',
        body: formData
    }).then(res => res.json()).then(data => {
        if (data.success) {
            showToast('Task marked as complete.');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast('Error completing task', true);
        }
    });
}

function submitRating(e, form) {
    e.preventDefault();
    const formData = new FormData(form);
    
    fetch('/rate', {
        method: 'POST',
        body: formData
    }).then(res => res.json()).then(data => {
        if (data.success) {
            showToast('Rating submitted successfully!');
            closeModal('rateModal' + formData.get('task_id'));
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast(data.message || 'Error submitting rating', true);
        }
    });
}

function shortlistStudent(btn, studentId) {
    const formData = new FormData();
    formData.append('student_id', studentId);

    fetch('/api/shortlist', {
        method: 'POST',
        body: formData
    }).then(res => res.json()).then(data => {
        if (data.success) {
            btn.innerText = 'Shortlisted ✓';
            btn.classList.add('btn-success');
            btn.disabled = true;
            showToast('Student shortlisted!');
        } else {
            showToast('Error shortlisting student', true);
        }
    });
}

function toggleReview(btn, flagId) {
    fetch('/admin/flags/review/' + flagId, {
        method: 'POST'
    }).then(res => res.json()).then(data => {
        if (data.success) {
            showToast('Flag review status updated');
        } else {
            showToast('Error updating status', true);
            btn.checked = !btn.checked; // revert
        }
    });
}
