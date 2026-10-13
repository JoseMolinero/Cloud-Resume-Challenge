(function() {
	'use strict';

	const btnES = document.getElementById('btn-es');
	const btnIN = document.getElementById('btn-in');
	const privacyNotices = document.querySelectorAll('.privacy-notice');

	function closePrivacyNotices() {
		privacyNotices.forEach(notice => notice.open = false);
	}

	document.addEventListener('click', function(e) {
		const closeButton = e.target.closest('.privacy-close');
		if (closeButton) {
			const notice = closeButton.closest('.privacy-notice');
			notice.open = false;
			notice.querySelector('summary').focus();
			return;
		}
		privacyNotices.forEach(notice => {
			if (!notice.contains(e.target)) notice.open = false;
		});
	});

	document.addEventListener('keydown', function(e) {
		if (e.key === 'Escape') {
			const openNotice = document.querySelector('.privacy-notice[open]');
			closePrivacyNotices();
			if (openNotice) openNotice.querySelector('summary').focus();
		}
	});

	window.addEventListener('hashchange', closePrivacyNotices);

	function toggleLanguage(lang) {
		closePrivacyNotices();
		const spanish = lang === 'ES';
		document.documentElement.lang = spanish ? 'es' : 'en';
		document.title = spanish ? 'Jose Molinero - Currículum' : 'Jose Molinero - Resume';
		document.querySelectorAll('.idioma').forEach(el => el.hidden = !el.classList.contains(lang));
		btnES.classList.toggle('active', spanish);
		btnIN.classList.toggle('active', !spanish);
		btnES.setAttribute('aria-pressed', String(spanish));
		btnIN.setAttribute('aria-pressed', String(!spanish));
		document.querySelector('.logo img').alt = spanish ? 'Avatar de Jose Molinero' : 'Jose Molinero avatar';
		document.querySelectorAll('#main article .close').forEach(el => {
			el.textContent = spanish ? 'Cerrar' : 'Close';
			el.setAttribute('aria-label', spanish ? 'Cerrar sección' : 'Close section');
		});
		try { localStorage.setItem('resume-language', spanish ? 'es' : 'en'); } catch (error) {}
	}

	let initialLanguage = 'ES';
	try { if (localStorage.getItem('resume-language') === 'en') initialLanguage = 'IN'; } catch (error) {}
	toggleLanguage(initialLanguage);
	btnES.addEventListener('click', function() { toggleLanguage('ES'); });
	btnIN.addEventListener('click', function() { toggleLanguage('IN'); });

	async function updateCounter() {
		const counter = document.querySelector('.visitas');
		const counterIN = document.querySelector('.visitasIN');
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 8000);
		try {
			const response = await fetch('https://3bjzz7j3xfyug6ucqloeavdvgi0ztohp.lambda-url.eu-west-2.on.aws/', {
				method: 'POST',
				credentials: 'omit',
				cache: 'no-store',
				signal: controller.signal
			});
			if (!response.ok) throw new Error('Counter request failed');
			const data = await response.json();
			// Compatibilidad con la respuesta numérica de la Lambda anterior.
			const views = typeof data === 'number' ? data : data && data.views;
			if (!Number.isSafeInteger(views) || views < 0) throw new Error('Invalid counter response');
			counter.textContent = `Visitas: ${views}`;
			counterIN.textContent = `Views: ${views}`;
		} catch (error) {
			console.warn('El contador de visitas no está disponible.');
		} finally {
			clearTimeout(timeoutId);
		}
	}
	updateCounter();
})();
