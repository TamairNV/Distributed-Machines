import {Component, inject, signal} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import { environment } from '../../environments/environment';
@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.html',
})
export class LoginComponent {
  http = inject(HttpClient);
  router = inject(Router);

  userName = '';
  userPasskey = '';
  incorrect_login = signal('');
  isLoading = false;

  createUser() {
    if (this.isLoading) return;
    this.isLoading = true;
    this.incorrect_login.set('');

    const login_data = { name: this.userName, passkey: this.userPasskey };

    this.http.post(`${environment.apiUrl}/api/login-user`, login_data, { withCredentials: true })
      .subscribe({
        next: (response: any) => {
          this.isLoading = false;

          if (response.status === "success") {
            // SAVE THE TOKEN FOR TAURI
            if (response.token) {
              localStorage.setItem('access_token', response.token);
            }

            this.router.navigate(['/player-dashboard']).then(r => {});
          }
        },
        error: (err) => {
          this.isLoading = false;
          this.incorrect_login.set('Incorrect Login Information');
          console.error('Flask request failed:', err);
        }
      });
  }
}
