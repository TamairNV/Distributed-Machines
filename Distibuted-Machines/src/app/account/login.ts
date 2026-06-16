import {Component, inject, signal} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {Router, RouterLink} from '@angular/router';

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
    if (this.isLoading) {
      return;
    }
    this.isLoading = true;
    this.incorrect_login.set('');

    const login_data = { name: this.userName, passkey: this.userPasskey };

    this.http.post('/api/login-user', login_data,
      { withCredentials: true })
      .subscribe({
        next: (response: any) => {
          this.isLoading = false;
          console.log(response,response.received)
          if (response.received == "Wrong") {
            this.incorrect_login.set('Incorrect Login Information');
          } else {

            const profile = {
              id: response.received.id,
              name: this.userName,
            };

            console.log(profile)

            this.router.navigate(['/player-dashboard']).then(r => {});


            console.log('User Login successfully!', response);
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
