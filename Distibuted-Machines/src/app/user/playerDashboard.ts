import {Component, inject, OnInit, signal,ChangeDetectorRef} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { NgZone } from '@angular/core';


@Component({
  selector: 'app-ref',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './playerDashboard.html',
})


class PlayerDashboard implements OnInit {
  http = inject(HttpClient);
  router = inject(Router);
  prompt = null
  modelInstalled = true
  startButton = 'START'
  status = false
  currentImage: string = "NONE"
  currentID: string = "NONE"
  message = ""
  constructor(private route: ActivatedRoute,private cdr: ChangeDetectorRef,private ngZone: NgZone) {}
  ngOnInit() {
    this.message = "Getting Prompt"
    this.cdr.detectChanges()
    this.http.post('/api/get-prompt',{"data" : "Give me prompt"},{ withCredentials: true })
      .subscribe({
        next: (response: any) => {
          this.prompt = response.received
        }
      });
    this.getContributions()
  }

  start(){
    if(this.startButton === "STOPPING"){
      return
    }

    if(this.status){
      this.status = false
      this.startButton = 'STOPPING'
    }else{
      this.status = true
      this.startButton = 'STOP'
      this.get_image_batch(10)
    }
  }
  images : any = []
  get_image_batch(amount: number){
    if(!this.status){
      return
    }
    this.message = "Getting Images"
    this.cdr.detectChanges()
    const data = {"amount" : amount}
    this.http.post('/api/get-batch-photos',data,{ withCredentials: true })
      .subscribe({
        next: async (response: any) => {
          if(response.status == "Failed"){
            console.log("Images failed to get")
            return
          }
          this.images = response.received
          console.log(this.images)
          console.log("Checking Ollama")
          await this.checkOllama()
        }
      });
  }

  imageStore = new Map();
  async downloadAll(): Promise<void> {
    this.imageStore = new Map();
    this.message = "Downloading Images"
    this.cdr.detectChanges()
    try {
      const downloadPromises = this.images.map(async (file: string) => {
        try {
          const response = await fetch(`/static/images/spot_${file}.jpeg`, {
            method: 'GET',
            credentials: 'include'
          });
          if (!response.ok) throw new Error(`Server returned status: ${response.status}`);
          const blob = await response.blob();

          const myFile = new File([blob], `${file}.jpeg`, { type: 'image/jpeg' });

          this.imageStore.set(file, myFile);

          console.log(`Successfully buffered and saved: ${file}`);
          return file;

        } catch (innerError) {
          console.log(`Skipped missing image ID: ${file}`);
          return null;
        }
      });
      const results = await Promise.all(downloadPromises);

      const successfulImages = results.filter((id): id is string => id !== null);

      console.log(`Downloaded ${successfulImages.length} out of ${this.images.length} images. Starting LLM analysis...`);

      if (successfulImages.length > 0) {
        await this.analyzeLocalImages(successfulImages);
      } else {
        console.log("No valid images were found to analyze.");
      }

    } catch (error) {
      console.error("Batch system failed:", error);
    }
  }



  async checkOllama(): Promise<void> {
    try {
      this.message = "Checking Ollama"
      this.cdr.detectChanges()
      // This checks if Ollama is installed and running
      const healthCheck = await fetch('http://localhost:11434/');
      if (!healthCheck.ok) throw new Error("Ollama not running");

      const response = await fetch('http://localhost:11434/api/tags');
      const data = await response.json();

      // See if your model is in the list
      const hasModel = data.models.some((m: any) =>
        m.name === 'hf.co/RadioactiveAnt7/fpv-spotter' || m.name === 'fpv-spotter'
      );

      if (hasModel) {
        console.log("Model is installed and ready!");
        this.modelInstalled = true
        this.model_download_percentage = 100
        this.cdr.detectChanges()
        this.downloadAll()

      } else {
        console.log("Model missing! Need to trigger a download.");
        this.modelInstalled = false
        this.startButton = "Model is Downloading"
        this.pullModel()
      }

    } catch (error) {
      this.message = "Failed to connected to Ollama"
      this.cdr.detectChanges()
      console.error("Could not connect to Ollama. Is the Ollama app running?", error);
    }
  }



  protected model_download_percentage = 0
  async pullModel(): Promise<void> {
    this.message = "Downloading Model"
    this.cdr.detectChanges()
    console.log("Triggering model download...");

    const response = await fetch('http://localhost:11434/api/pull', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'hf.co/RadioactiveAnt7/fpv-spotter' })
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      console.log("Model is completely downloaded and ready!");
      this.modelInstalled = false
      break;
    }

    const textChunks = decoder.decode(value).split('\n').filter(Boolean);

    for (const chunk of textChunks) {
      const data = JSON.parse(chunk);
      console.log(this.model_download_percentage)
      if (data.total) {
        // percentage math for UI
        this.model_download_percentage = Math.round((data.completed / data.total) * 100);

      } else {
        console.log(data.status);
      }
      this.cdr.detectChanges()
    }
  }
    this.modelInstalled = true
    this.startButton = "STOP"
    this.downloadAll()
    this.cdr.detectChanges()

  }

  private async processSingleImage(id: string): Promise<void> {
    try {
      this.message = `Processing Image ${id}`
      this.cdr.detectChanges()
      const retrievedFile = this.imageStore.get(id);
      if (!retrievedFile) throw new Error(`No image found for ID: ${id}`);

// 1. Convert the raw Blob to Base64 (Required by Ollama)
      const base64Image = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(retrievedFile);
        reader.onloadend = () => {
          const result = reader.result as string;
          if (!result || !result.includes(',')) {
            reject(new Error("Invalid or empty image data URI generated."));
            return;
          }
          resolve(result.split(',')[1]); // Safely isolate only the raw base64 bytes
        };
        reader.onerror = reject;
      });

      let cleanPromptText = this.prompt;


      const modelData = {
        model: 'hf.co/RadioactiveAnt7/fpv-spotter',
        prompt: cleanPromptText,
        stream: false,
        images: [base64Image]
      };


      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modelData),
        credentials: 'omit' // Keeps Flask cookies away from Ollama
      });

      if (!response.ok) throw new Error(`Ollama status: ${response.status}`);

      const ollamaData = await response.json();

      console.log("Raw from Ollama:", ollamaData.response);

      const parsedAnalysis = this.extractJson(ollamaData.response);

      console.log("Successfully parsed object:", parsedAnalysis);

      await this.submitResultToBackend(id, parsedAnalysis);

      const localUrl = URL.createObjectURL(retrievedFile);
      await this.displayImage(localUrl);

      this.currentID = id;
      this.cdr.detectChanges();

    } catch (error) {
      console.error(`Failed to process image ${id}:`, error);
    }
  }
  private extractJson(rawText: string): any {
    this.message = `Extracing Scores`
    this.cdr.detectChanges()
    const jsonMatch = rawText.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
    if (!jsonMatch) {
      throw new Error("Could not find any JSON structure in the AI output.");
    }
    return JSON.parse(jsonMatch[0]);
  }

  async analyzeLocalImages(imageIds: string[]): Promise<void> {
    const BATCH_SIZE = 1;
    this.message = `Starting Batch`
    this.cdr.detectChanges()
    console.log(`Starting AI analysis in batches of ${BATCH_SIZE}...`);

    for (let i = 0; i < imageIds.length; i += BATCH_SIZE) {
      const chunk = imageIds.slice(i, i + BATCH_SIZE);
      console.log(`Processing batch ${Math.floor(i / BATCH_SIZE) + 1}...`);
      const batchPromises = chunk.map(id => this.processSingleImage(id));

      await Promise.all(batchPromises);
    }

    console.log("All image batches successfully analyzed!");
    this.getContributions();
    if(this.status){
      this.get_image_batch(10)
    }else{
      this.startButton = "START"
      this.status = false
      this.cdr.detectChanges();
    }
  }

  private bytesToBase64(bytes: Uint8Array): string {
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private async submitResultToBackend(id: string, data: any) {
    console.log(data,id)
    this.message = `Sending Scores`
    this.cdr.detectChanges()
    this.http.post('/api/submit-results',{ imageId: id, analysis: data },{ withCredentials: true })
      .subscribe({
        next: (response: any) => {
          if(response.status == "Failed"){
            console.log("scores failed to save")
            return
          }
          else{
            console.log("scores Logged")
            this.user_con +=1
            this.cdr.detectChanges();
          }
        }
      });
  }
  protected totalProgress = 0
  protected user_con = 0
  getContributions(){
    this.message = `Getting Contributions`
    this.cdr.detectChanges()
    this.http.post('/api/get-contributions',{"data" : "Give me prompt"},{withCredentials: true})
      .subscribe({
        next: (response: any) => {
          console.log(response)
          this.totalProgress =  Number(response['total_progress'][0]['percent_completed'])
          this.user_con = response['user_con'][0]['COUNT(*)']
          this.cdr.detectChanges();
        }
      });
  }

  async displayImage(relativePath: string): Promise<void> {
    try {
      this.currentImage = relativePath;

    } catch (error) {
      console.error("Failed to load image for UI:", error);
    }
  }



}

export default PlayerDashboard;



