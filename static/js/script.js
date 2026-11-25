// ===== Header / nav / back-to-top =====
const header = document.getElementById('siteHeader');
const toTopBtn = document.getElementById('toTop');
const hamburger = document.getElementById('hamburger');
const mainNav = document.getElementById('mainNav');

if (hamburger && mainNav) {
  hamburger.addEventListener('click', () => {
    mainNav.classList.toggle('open');
    hamburger.classList.toggle('open');
  });
  mainNav.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      mainNav.classList.remove('open');
      hamburger.classList.remove('open');
    });
  });
}

// ===== Active nav link on scroll =====
const sections = [...document.querySelectorAll('section[id]')];
const navLinks = [...document.querySelectorAll('.nav-link')];

function updateActiveNav() {
  let current = sections[0]?.id;
  const scrollPos = window.scrollY + 140;
  sections.forEach(sec => {
    if (sec.offsetTop <= scrollPos) current = sec.id;
  });
  navLinks.forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === `#${current}`);
  });
}

function onScroll() {
  const y = window.scrollY;
  if (header) header.classList.toggle('scrolled', y > 20);
  if (toTopBtn) toTopBtn.classList.toggle('show', y > 500);
  updateActiveNav();
}
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

if (toTopBtn) {
  toTopBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

// ===== Scroll reveal =====
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in-view');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
document.querySelectorAll('[data-reveal]').forEach(el => revealObserver.observe(el));

// ===== Skill bar animation trigger =====
const skillObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in-view');
      skillObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });
document.querySelectorAll('.skill-card').forEach(card => skillObserver.observe(card));

// ===== Role rotator =====
document.addEventListener('DOMContentLoaded', () => {
  const roles = document.querySelectorAll('.role');
  if (roles.length < 2) return;
  let index = 0;
  setInterval(() => {
    roles[index].classList.remove('active');
    index = (index + 1) % roles.length;
    roles[index].classList.add('active');
  }, 2000);
});

// ===== Helpers =====
function resetCaptcha(form) {
  try {
    const box = form && form.querySelector('.cf-turnstile');
    if (window.turnstile && box) window.turnstile.reset(box);
  } catch (e) { /* ignore */ }
}

// ===== Generic AJAX forms (quote, review, newsletter): <form data-ajax data-success="..."> =====
document.querySelectorAll('form[data-ajax]').forEach(form => {
  const msg = form.querySelector('.form-msg');
  const labelEl = form.querySelector('.btn-label');
  const button = form.querySelector('button[type="submit"]');

  function show(text, ok) {
    if (!msg) return;
    msg.textContent = text;
    msg.classList.add('show');
    msg.classList.toggle('error', !ok);
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const original = labelEl ? labelEl.textContent : '';
    if (button) button.disabled = true;
    if (labelEl) labelEl.textContent = 'Sending...';
    if (msg) msg.classList.remove('show');
    try {
      const res = await fetch(form.action, {
        method: 'POST', body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.ok) {
        show(form.dataset.success || 'Done!', true);
        form.reset();
      } else {
        show(data.error || 'Something went wrong. Please try again.', false);
      }
    } catch (err) {
      show('Network error. Please check your connection and try again.', false);
    } finally {
      resetCaptcha(form);
      if (button) button.disabled = false;
      if (labelEl) labelEl.textContent = original;
    }
  });
});

// ===== Contact form -> Django backend (saved in DB + email notification) =====
const contactForm = document.getElementById('contactForm');
const contactSubmit = document.getElementById('contactSubmit');
const contactSuccess = document.getElementById('contactSuccess');
const verificationBox = document.getElementById('verificationBox');

function showFormMessage(text, ok) {
  if (!contactSuccess) return;
  contactSuccess.textContent = text;
  contactSuccess.classList.add('show');
  contactSuccess.style.color = ok ? '' : '#ff7a7a';
  contactSuccess.style.borderColor = ok ? '' : 'rgba(255,122,122,.3)';
  contactSuccess.style.background = ok ? '' : 'rgba(255,122,122,.06)';
}

if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const label = contactSubmit.querySelector('span:first-child');
    const originalLabel = label.textContent;
    contactSubmit.disabled = true;
    label.textContent = 'Sending...';
    contactSuccess.classList.remove('show');

    try {
      const response = await fetch(contactForm.action, {
        method: 'POST',
        body: new FormData(contactForm),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await response.json().catch(() => ({}));

      if (response.ok && data.ok) {
        showFormMessage('✓ Thank you! Your message has been sent. I will get back to you soon.', true);
        contactForm.reset();
        resetCaptcha(contactForm);
      } else {
        showFormMessage(data.error || 'Something went wrong. Please try again.', false);
        resetCaptcha(contactForm);
      }
    } catch (err) {
      showFormMessage('Network error. Please check your connection and try again.', false);
    } finally {
      contactSubmit.disabled = false;
      label.textContent = originalLabel;
    }
  });
}
